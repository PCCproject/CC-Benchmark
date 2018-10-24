#!/usr/bin/python3
import os
from setup import pantheon_setup
from graphing.graph_utils import convert_pantheon_log
from python_utils import file_locations
from python_utils.test_utils import read_topology_to_dict, read_test_list_to_list, read_test_to_dict
import subprocess
import sys
import time
import json
import datetime
import random
mininet_dir = "/home/pcc/mininet/"
sys.path.append(mininet_dir)
from examples import sshd
from mininet.link import TCLink
from mininet.net import Mininet

data_dir = "/tmp/pcc_automated_testing/data/"

username = "pcc"

def get_free_run_id():
    return random.randint(0, 2e9)

def run_test(test_dict):
    test_name = "temp_test_name"
    date_string = datetime.date.today().strftime("%B_%d_%Y") + "_%d" % (int(round(time.time() * 1000)))
    results_dir = os.path.join(file_locations.results_dir, test["Name"], "%s_%s" % (test_name, date_string))
    os.system("mkdir -p %s" % results_dir)
    test_topo_name = test_dict["Topology"]
    test_topo_dict = read_topology_to_dict(test_topo_name)
    net = Mininet(topo=sshd.MyTopo(test_topo_dict), link=TCLink)
    sshd.sshd(net)
    flows = test_dict["Flows"]
    run_ids = {}
    for i in range(0, len(flows)):
        flow = flows[i]
        run_id = run_ids[i] = get_free_run_id()
        if flow["protocol"] == "TEST":
            flow["protocol"] = "pcc_test_scheme"
        test_command = "%s/test/test.py remote --start-run-id %d --data-dir %s --schemes %s %s:%s" % (pantheon_setup.pan_dir, run_id, data_dir, 
            flow["protocol"], flow["dst"], pantheon_setup.pan_dir)
        os.system("sudo -u %s ssh -i ~/.ssh/id_mininet_rsa %s \"%s\" &" % (username, flow["src"], test_command))
    time.sleep(40)
    net.stop()
    os.system("mn -c")

    for i in range(0, len(flows)):
        flow = flows[i]
        run_id = run_ids[i]
        convert_pantheon_log("%s/%s_datalink_run%d.log" % (data_dir, flow["protocol"], run_id),
            "%s/%s_%s.json" % (results_dir, flow["protocol"], flow["name"]))

    graphing_script = os.path.join(pantheon_setup.pan_dir, "..", "graphing", "pcc_grapher.py")
    graph_config = os.path.join(pantheon_setup.pan_dir, "..", "graphing", "graphs", "sample.json")
    #os.system("python %s %s %s" % (graphing_script, results_dir, graph_config))

##
#   Load in the test descriptor files.
##

tests_to_run = sys.argv[2]
all_test_names = read_test_list_to_list(tests_to_run)
all_tests = [read_test_to_dict(t) for t in all_test_names]

##
#   Begin executing tests. Note: Eventually tests should be grouped by topology so
#   each test doesn't require a restart of mininet, and so tests can be scheduled
#   better.
##

for test in all_tests:
    run_test(test)
