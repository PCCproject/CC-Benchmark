#!/usr/bin/python

"""
Create a network and start sshd(8) on each host.

While something like rshd(8) would be lighter and faster,
(and perfectly adequate on an in-machine network)
the advantage of running sshd is that scripts can work
unchanged on mininet and hardware.

In addition to providing ssh access to hosts, this example
demonstrates:

- creating a convenience function to construct networks
- connecting the host network to the root namespace
- running server processes (sshd in this case) on hosts
"""

import sys
import time
import random

from mininet.topo import Topo
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.node import Node
from mininet.topolib import TreeTopo
from mininet.util import waitListening

import multiprocessing
import hashlib

SWITCH_SIDE = "SW"
HOST_SIDE = "H"

def TreeNet( depth=1, fanout=2, **kwargs ):
    "Convenience function for creating tree networks."
    topo = TreeTopo( depth, fanout )
    return Mininet( topo, **kwargs )

def connectToRootNS( network, switch, ip, routes ):
    """Connect hosts to root namespace via switch. Starts network.
      network: Mininet() network object
      switch: switch to connect to root namespace
      ip: IP address for root namespace node
      routes: host networks to route to"""
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    intf = network.addLink( root, switch ).intf1
    root.setIP( ip, intf=intf )
    print("ROOT IFCONFIGGGGGG\n\n\n")
    print(root.cmd('ifconfig'))
    #print(network.get('root').cmd('ifconfig'))
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        print('route add -net ' + route + ' dev ' + str( intf ))
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )

def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    if not switch:
        names = network.keys()
        switch = None
        for name in names:
            if (switch is None) and (name[0] == "L"):
                switch = network[name]
        print("Switch is %s" % switch)
    if not routes:
        routes = [ '10.0.0.0/24' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        print(host)
        host.cmd( cmd + ' ' + opts + '&' )
    for server in network.hosts:
        #print(help(server))
        #print(server.intfList())
        waitListening( server=server, port=22, timeout=5 )
    #waitListening( server='10.0.1.1', port=22, timeout=5 )
    #waitListening( server='10.0.1.2', port=22, timeout=5 )

    for host in network.hosts:
        info( host.name, host.IP(), '\n' )
        print( host.name, host.IP(), '\n' )

def oscillate_half_bw(link, link_def, link_state, intf_side):
    bw = link_state["bw"]
    if bw == link_def["bw"]:
        new_bw = link_def["bw"] * 0.5
    else:
        new_bw = link_def["bw"]
    link_state["bw"] = new_bw
    if intf_side == HOST_SIDE:
        cmds, parent = link.intf1.bwCmds(bw=new_bw)
        cmd = cmds[1].replace("add", "change")
        link.intf1.tc(cmd)
    else:
        cmds, parent = link.intf2.bwCmds(bw=new_bw)
        cmd = cmds[1].replace("add", "change")
        link.intf2.tc(cmd)
    return link_state

def custard_variable_link(link, link_def, link_state, intf_side):
    print("Running variable link for %s" % str(link))
    bw = random.randint(16, 32)
    if intf_side == HOST_SIDE:
        cmds, parent_1 = link.intf1.bwCmds(bw=bw)
        cmd = cmds[1].replace("add", "change")
        link.intf1.tc(cmd)
    else:
        cmds, parent_2 = link.intf1.bwCmds(bw=bw)
        cmd = cmds[1].replace("add", "change")
        link.intf2.tc(cmd)

def nsdi_variable_link(link, link_def, link_state, intf_side):
    bw = random.randint(10, 100)
    dl = random.uniform(10, 100)
    lr = 100.0 * random.uniform(0.0, 0.01)
    if intf_side == HOST_SIDE:
        cmds, parent_1 = link.intf1.bwCmds(bw=bw)
        cmd = cmds[1].replace("add", "change")
        link.intf1.tc(cmd)
        cmds, parent_2 = link.intf2.bwCmds(bw=bw)
        cmds, parent = link.intf2.delayCmds(parent_2, delay="%fms" % dl, loss=lr)
        cmd = cmds[0].replace("add", "change")
        link.intf2.tc(cmd)
    else:
        cmds, parent_2 = link.intf2.bwCmds(bw=bw)
        cmd = cmds[1].replace("add", "change")
        link.intf2.tc(cmd)
        cmds, parent_1 = link.intf1.bwCmds(bw=bw)
        cmds, parent = link.intf1.delayCmds(parent_1, delay="%fms" % dl, loss=lr)
        cmd = cmds[0].replace("add", "change")
        link.intf1.tc(cmd)

LINK_VARIATION_FUNCS = {
    "oscillate_half_bw":oscillate_half_bw,
    "nsdi_variable_link":nsdi_variable_link,
    "custard_variable_link":custard_variable_link
}

def get_initial_link_state(link_def):
    state = {}
    state["bw"] = link_def["bw"]
    return state

class LinkManager():

    def __init__(self, link, link_def, intf_side):
        self.link = link
        self.link_def = link_def
        self.intf_side = intf_side
        self.variation_func = None
        self.variation_period = None
        if "variation" in link_def.keys():
            self.variation_func = LINK_VARIATION_FUNCS[link_def["variation"]["func"]]
            self.variation_period = link_def["variation"]["period"]
        self.link_state = get_initial_link_state(link_def)
        self.done = multiprocessing.Value('i')
        self.done.value = 0
        self.cur_bw = 10
        self.proc = multiprocessing.Process(target=self.run, args=(0, 0))
        self.running = False
        if (self.variation_func is not None):
            self.running = True
            self.proc.start()

    def run(self, dummy1, dummy2):
        time_offset = time.time()
        next_variation = 1
        while (self.done.value == 0):
            next_oscillation_time = time_offset + next_variation * self.variation_period
            sleep_time = next_oscillation_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            print("Running variation %d" % next_variation)
            self.link_state = self.variation_func(self.link, self.link_def, self.link_state, self.intf_side)
            next_variation += 1

    def stop(self):
        if (self.running):
            self.done.value = 1
            self.proc.terminate()
            self.proc.join()

class MyTopo(Topo):

    def get_entity_by_name(self, name, switches, hosts):
        if (name in switches.keys()):
            return switches[name]

        if (name in hosts.keys()):
            return hosts[name]

        print("ERROR: Could not find switch or host named %s" % name)
        return None

    def add_bw_queue_link(self, link_type, src, dst):
        lt = link_type
        loss = 100.0 * lt["loss"] if "loss" in lt.keys() else 0.0
        bw = lt["bw"] if "bw" in lt.keys() else None
        queue = lt["queue"] if "queue" in lt.keys() else None

        new_link = self.addLink(src, dst, bw=bw, max_queue_size=queue, loss=loss)

    def add_dl_link(self, link_type, src, dst):
        lt = link_type

        jitter = lt["jitter"] if "jitter" in lt.keys() else None
        delay = lt["dl"] if "dl" in lt.keys() else None
        bw = lt["bw"] if "bw" in lt.keys() else None
        passthrough_bw = None if bw is None else 4 * bw

        bdp_queue_size = None
        if delay is not None:
            delay_sec = int(delay[:-2]) / 1000.0
            bw_bps = 2 * passthrough_bw * 1e6
            bdp_queue_size = bw_bps * delay_sec / (1500.0 * 8.0)

        new_link = self.addLink(src, dst, bw=passthrough_bw, delay=delay,
                max_queue_size=bdp_queue_size, jitter=jitter)

    def get_switch_name(self, link_def):
        src_dst_str = ("%s-%s" % (link_def["src"], link_def["dst"])).encode('utf-8')
        name = hashlib.md5(src_dst_str).hexdigest()[-4:]
        return "%s-%s" % (link_def["type"], name)

    def add_link_by_def(self, link_def, link_types, switches, hosts):
        src = self.get_entity_by_name(link_def["src"], switches, hosts)
        dst = self.get_entity_by_name(link_def["dst"], switches, hosts)

        switch_name = self.get_switch_name(link_def)
        link_switch = self.addSwitch(switch_name)

        link_type = link_types[link_def["type"]]

        self.add_bw_queue_link(link_type, src, link_switch)
        self.add_dl_link(link_type, link_switch, dst)

    def build(self, topo_dict, link_types):
        # print(topo_dict)
        # print(link_types)
        self.topo_dict = topo_dict
        self.link_types = link_types
        self.link_managers = []
        switch_defs = []
        if "Switches" in topo_dict.keys():
            switch_defs = topo_dict["Switches"]
        host_defs = topo_dict["Hosts"]
        link_defs = topo_dict["Links"]

        switches = {}
        for switch_def in switch_defs:
            switches[switch_def["Name"]] = self.addSwitch(switch_def["Name"])

        hosts = {}
        for host_def in host_defs:
            hosts[host_def["Name"]] = self.addHost(host_def["Name"])

        for link_def in link_defs:
            self.add_link_by_def(link_def, link_types, switches, hosts)

    def get_net_link_type(self, link):
        link_str = str(link)
        if link_str[0] == "L":
            return SWITCH_SIDE, link_str.split("-")[0]
        else:
            return HOST_SIDE, link_str.split("<->")[1].split("-")[0]

    def start_all_link_managers(self, net):
        for link in net.links:
            if "root" in ("%s" % link):
                continue
            print(link)
            intf_side, link_type = self.get_net_link_type(link)
            #if not link_type[0] == "L":
            #    continue
            print("Found net link type %s" % link_type)
            self.link_managers.append(LinkManager(link, self.link_types[link_type], intf_side))

    def stop_all_link_managers(self):
        for link_manager in self.link_managers:
            print("Stopping link manager")
            link_manager.stop()

    def print_all_links(self, net):
        print("Printing links")
        for link in self.topo_dict["Links"]:
            print(link)
        for link in net.links:
            print(link)
