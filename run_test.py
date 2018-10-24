#!/usr/bin/python3
import os
from setup import pantheon_setup
from graphing.graph_utils import convert_pantheon_log
import subprocess
import sys
import time
import json
import datetime
import random

mininet_dir = "/home/pcc/mininet/"
testing_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
data_dir = "/tmp/pcc_automated_testing/data/"
results_base_dir = os.path.join(testing_dir, "results")
#os.system("mkdir -p %s" % data_dir)
sys.path.append(mininet_dir)
from examples import sshd
from mininet.link import TCLink
from mininet.net import Mininet

username = "pcc"

def load_topology(topology_name):
    topo_file = os.path.join(testing_dir, "topos", topology_name + ".json")
    topo_json = None
    with open(topo_file) as f:
        topo_json = json.load(f)
    return topo_json

def get_free_run_id():
    return random.randint(0, 2e9)

def run_test(test_dict):
    print(test_dict)
    test_name = "temp_test_name"
    date_string = datetime.date.today().strftime("%B_%d_%Y") + "_%d" % (int(round(time.time() * 1000)))
    results_dir = os.path.join(results_base_dir, test["Name"], "%s_%s" % (test_name, date_string))
    os.system("mkdir -p %s" % results_dir)
    test_topo_name = test_dict["Topology"]
    test_topo_dict = load_topology(test_topo_name)
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
        #os.system("chmod 666 %s/%s_%d.json" % (results_dir, flow["protocol"], run_id))

    graphing_script = os.path.join(pantheon_setup.pan_dir, "..", "graphing", "pcc_grapher.py")
    graph_config = os.path.join(pantheon_setup.pan_dir, "..", "graphing", "graphs", "sample.json")
    #os.system("python %s %s %s" % (graphing_script, results_dir, graph_config))

##
#   Load in the test descriptor files.
##

test_file = os.path.join(testing_dir, "tests", sys.argv[2]) + ".json"
test_json = None
with open(test_file) as f:
    test_json = json.load(f)
print("Loaded test (list) from %s" % test_file)

all_tests = []
if "Tests" in test_json.keys():
    test_filenames = test_json["Tests"]
    for test_filename in test_filenames:
        test_file = os.path.join(testing_dir, "tests", test_filename) + ".json"
        test_json = None
        with open(test_file) as f:
            test_json = json.load(f)
        print("Loaded test from %s" % test_file)
        all_tests.append(test_json)
else:
    all_tests = [test_json]

##
#   Begin executing tests. Note: Eventually tests should be grouped by topology so
#   each test doesn't require a restart of mininet, and so tests can be scheduled
#   better.
##

print(all_tests)
for test in all_tests:
    print(test)
    run_test(test)
