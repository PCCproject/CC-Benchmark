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

from mininet.topo import Topo
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.node import Node
from mininet.topolib import TreeTopo
from mininet.util import waitListening

import multiprocessing

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
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )

def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    if not switch:
        switch = network[ 's1' ]  # switch to use
    if not routes:
        routes = [ '10.0.0.0/24' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    for server in network.hosts:
        waitListening( server=server, port=22, timeout=5 )

    for host in network.hosts:
        info( host.name, host.IP(), '\n' )

class LinkManager():
    
    def __init__(self, link):
        self.link = link
        self.done = multiprocessing.Value('i')
        self.done.value = 0
        self.cur_bw = 10
        self.proc = multiprocessing.Process(target=self.run, args=(0, 0))
        self.proc.start()

    def run(self, dummy1, dummy2):
        # Do nothing, for now

        """
        while (self.done.value == 0):
            time.sleep(5)
            if (self.cur_bw == 10):
                self.cur_bw = 5
            else:
                self.cur_bw = 10
            cmds, parent = self.link.intf1.bwCmds(bw=self.cur_bw)
            cmd = cmds[1].replace("add", "change")
            print("Changing bandwidth with command:")
            print(cmd)
            self.link.intf1.tc(cmd)
            #cmds, parent = self.link.intf2.bwCmds(bw=self.cur_bw)
            #self.link.intf2.tc(cmds)
        """

    def stop(self):
        self.done.value = 1
        self.proc.join()

class MyTopo(Topo):

    def get_entity_by_name(self, name, switches, hosts):
        if (name in switches.keys()):
            return switches[name]

        if (name in hosts.keys()):
            return hosts[name]

        print("ERROR: Could not find switch or host named %s" % name)
        return None

    def add_link_by_def(self, link_def, link_types, switches, hosts):
        src = self.get_entity_by_name(link_def["src"], switches, hosts)
        dst = self.get_entity_by_name(link_def["dst"], switches, hosts)

        loss = 0.0
        if "loss" in link_def.keys():
            loss = float(link_def["loss"])
        this_link_type = link_types[link_def["type"]]
        new_link = self.addLink(src, dst, bw=int(this_link_type["bw"]),
            delay=this_link_type["dl"], max_queue_size=int(this_link_type["queue"]),
            loss=loss)

    def build(self, topo_dict, link_types):
        self.topo_dict = topo_dict
        self.link_types = link_types
        self.link_managers = []
        switch_defs = topo_dict["Switches"]
        host_defs = topo_dict["Hosts"]
        link_defs = topo_dict["Links"]

        switches = {}
        for switch_def in switch_defs:
            switches[switch_def["Name"]] = self.addSwitch(switch_def["Name"])
            print("Added switch %s" % (switch_def["Name"]))

        print("Checking for hosts, expect to make %d" % len(host_defs))
        print("Topology: %s" % str(topo_dict))
        hosts = {}
        for host_def in host_defs:
            hosts[host_def["Name"]] = self.addHost(host_def["Name"])
            print("Added host %s" % host_def["Name"])

        for link_def in link_defs:
            self.add_link_by_def(link_def, link_types, switches, hosts)

    def start_all_link_managers(self, net):
        for link in net.links:
            if "root" in ("%s" % link):
                continue
            self.link_managers.append(LinkManager(link))

    def stop_all_link_managers(self):
        for link_manager in self.link_managers:
            link_manager.stop()

    def print_all_links(self, net):
        print("Printing links")
        for link in self.topo_dict["Links"]:
            print(link)
        for link in net.links:
            print(link)
