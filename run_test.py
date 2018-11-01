#!/usr/bin/python3
import os
from python_utils import file_locations
from python_utils import test_utils
from python_utils import pantheon_setup
from python_utils.test_utils import read_topology_to_dict
from python_utils.test_utils import read_test_list_to_list
from python_utils.test_utils import read_test_to_dict
from python_utils.pantheon_log_conversion import convert_pantheon_log
import subprocess
import sys
import time
import json
import datetime
import random
mininet_dir = "/home/pcc/mininet/"
sys.path.append(mininet_dir)
from python_utils import mininet_utils
from mininet.link import TCLink
from mininet.net import Mininet

scheme_to_test = sys.argv[1]
tests_to_run = sys.argv[2]
extra_args = None
if (len(sys.argv) > 3):
    extra_args = sys.argv[3].split(' ')

if (scheme_to_test not in test_utils.SUPPORTED_PANTHEON_SCHEMES):
    scheme_to_test = pantheon_setup.add_scheme_to_pantheon(scheme_to_test, extra_args)

data_dir = "/tmp/pcc_automated_testing/data/"
username = "pcc"

def sort_by_start_time(flows):
    for flow in flows:
        if "start" not in flow.keys():
            flow["start"] = 0.0

    return sorted(flows, key=lambda k: k["start"])

def get_free_run_id():
    return random.randint(0, 2e9)

def run_test(test_dict):
    date_string = datetime.date.today().strftime("%B_%d_%Y") + "_%d" % (int(round(time.time() * 1000)))
    results_dir = os.path.join(file_locations.results_dir, test["Name"], date_string)
    os.system("mkdir -p %s" % results_dir)
    test_topo_dict = read_topology_to_dict(test_dict["Topology"])
    test_link_types = test_dict["Link Types"]
    topo = mininet_utils.MyTopo(test_topo_dict, test_link_types)
    net = Mininet(topo=topo, link=TCLink)
    mininet_utils.sshd(net)
    topo.start_all_link_managers(net)
    flows = sort_by_start_time(test_dict["Flows"])
    run_ids = {}
    max_end = 0
    cur_time = 0.0
    for i in range(0, len(flows)):
        flow = flows[i]
        run_id = run_ids[i] = get_free_run_id()
        if flow["protocol"] == "TEST":
            flow["protocol"] = scheme_to_test
        run_dur = 30
        if ("dur" in flow.keys()):
            run_dur = flow["dur"]
        run_end = flow["start"] + run_dur
        if (run_end > max_end):
            max_end = run_end
        sleep_dur = flow["start"] - cur_time
        if (sleep_dur > 0.0):
            time.sleep(sleep_dur)
            cur_time += sleep_dur
        test_command = "%s/test/test.py remote -t %d --start-run-id %d --data-dir %s --schemes %s %s:%s" % (file_locations.pantheon_dir, run_dur, run_id, data_dir, 
            flow["protocol"], flow["dst"], file_locations.pantheon_dir)
        os.system("sudo -u %s ssh -i ~/.ssh/id_mininet_rsa %s \"%s\" &" % (username, flow["src"], test_command))
    time.sleep(30 + max_end - cur_time)
    topo.stop_all_link_managers()
    net.stop()
    os.system("mn -c")

    for i in range(0, len(flows)):
        flow = flows[i]
        run_id = run_ids[i]
        log_name = "%s/%s_datalink_run%d.log" % (data_dir, flow["protocol"], run_id)
        saved_name = "%s/%s_datalink.%s.log" % (results_dir, flow["protocol"], flow["name"]) 
        converted_name = "%s/%s.%s.json" % (results_dir, flow["protocol"], flow["name"])
        os.system("cp %s %s" % (log_name, saved_name))
        convert_pantheon_log(log_name, converted_name) 

    metadata = {
        "Scheme":scheme_to_test,
        "Finish Time":int(round(time.time() * 1000))
    }
    with open(os.path.join(results_dir, "test_metadata.json"), "w") as f:
        json.dump(metadata, f)
    os.system("rm -rf %s/*" % data_dir)

    graphing_script = os.path.join(file_locations.graphing_dir, "pcc_grapher.py")
    graph_config = os.path.join(file_locations.graphing_dir, "..", "graphing", "graphs", "sample.json")
    #os.system("python %s %s %s" % (graphing_script, results_dir, graph_config))

##
#   Load in the test descriptor files.
##

all_test_names = read_test_list_to_list(tests_to_run)
all_tests = [read_test_to_dict(t) for t in all_test_names]

##
#   Begin executing tests. Note: Eventually tests should be grouped by topology so
#   each test doesn't require a restart of mininet, and so tests can be scheduled
#   better.
##

for test in all_tests:
    run_test(test)
