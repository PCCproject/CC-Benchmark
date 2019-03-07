#!/usr/bin/python3
from python_utils.test_utils import read_topology_to_dict
from python_utils.test_utils import read_test_list_to_list
from python_utils.test_utils import read_test_to_dict
import subprocess
import sys
import time
mininet_dir = "/home/pcc/mininet/"
sys.path.append(mininet_dir)
from python_utils import mininet_utils
from mininet.link import TCLink
from mininet.net import Mininet

default_build_dir = "/home/pcc/pcc_test_scheme/"

tests_to_run = sys.argv[1]

username = "pcc"

def run_net_for_test(test_dict):
    print("Removing any running mininet instance.")
    mininet_clean_output = subprocess.check_output(["sudo", "mn", "-c"])
    test_topo_dict = read_topology_to_dict(test_dict["Topology"])
    test_link_types = test_dict["Link Types"]
    topo = mininet_utils.MyTopo(test_topo_dict, test_link_types)
    net = Mininet(topo=topo, link=TCLink)
    mininet_utils.sshd(net)
    topo.start_all_link_managers(net)
    while True:
        time.sleep(1.0)

##
#   Load in the test descriptor files.
##

all_test_names = read_test_list_to_list(tests_to_run)
all_tests = [read_test_to_dict(t) for t in all_test_names]

##
#   Run the network for each test. Right now, this only runs the network for the first test, then
#   it waits to be killed.
##

try:
    for test in all_tests:
        run_net_for_test(test)
except Exception as e:
    print(e)
