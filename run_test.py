#!/usr/bin/python3
import os
from python_utils import file_locations
from python_utils import test_utils
from python_utils import pantheon_setup
from python_utils import github_utils
from python_utils import ssh_utils
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

default_build_dir = "/home/pcc/pcc_test_scheme/"
scheme_to_test = sys.argv[1]

is_git_repo = False
git_repo = None
git_branch = None
git_checksum = None

# This means we are testing a branch from a repository -- we probably have to build it first
if (":" in scheme_to_test):
    is_git_repo = True
    parts = scheme_to_test.split(":")
    repo = parts[0]
    branch = parts[1]

    # Check if a repo exists in the usual build location
    if (os.path.isdir(os.path.join(default_build_dir, ".git"))):

        # We have a build dir, but we may not have the correct repo or branch.
        if (not github_utils.dir_has_repo(repo, branch, default_build_dir)):
            git_checksum = github_utils.build_repo_in_dir(repo, branch, default_build_dir)
        else:
            git_checksum = github_utils.get_repo_checksum(default_build_dir)
    else:
        # No dir? Make it and clone there
        os.system("mkdir -p %s" % default_build_dir)
        git_checksum = github_utils.build_repo_in_dir(repo, branch, default_build_dir)
    scheme_to_test = os.path.join(default_build_dir, "src")

    git_repo = repo
    git_branch = branch

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

def wait_for_all_logs_or_timeout(log_names, timeout):
    next_log_to_check = 0
    start_wait_time = time.time()
    time_waited = 0.0
    while time_waited < timeout and next_log_to_check < len(log_names):
        waiting_for_file = False
        while next_log_to_check < len(log_names) and not waiting_for_file:
            if os.path.exists(log_names[next_log_to_check]):
                next_log_to_check += 1
            else:
                waiting_for_file = True
        time.sleep(1.0)
        time_waited = time.time() - start_wait_time
    if next_log_to_check < len(log_names):
        return False
    return True

def run_test(test_dict):
    date_string = datetime.date.today().strftime("%B_%d_%Y") + "_%d" % (int(round(time.time() * 1000)))
    results_dir = os.path.join(file_locations.results_dir, test["Name"], date_string)
    os.system("mkdir -p %s" % results_dir)
    print("Removing any running mininet instance.")
    mininet_clean_output = subprocess.check_output(["sudo", "mn", "-c"])
    test_topo_dict = read_topology_to_dict(test_dict["Topology"])
    test_link_types = test_dict["Link Types"]
    topo = mininet_utils.MyTopo(test_topo_dict, test_link_types)
    net = Mininet(topo=topo, link=TCLink)
    mininet_utils.sshd(net)
    topo.start_all_link_managers(net)
    flows = sort_by_start_time(test_dict["Flows"])
    run_ids = {}
    max_end = 0
    time_offset = time.time()
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
        sleep_dur = flow["start"] + time_offset - time.time()
        if (sleep_dur > 0.0):
            time.sleep(sleep_dur)
        test_command = "%s/test/test.py remote -t %d --start-run-id %d --data-dir %s --schemes %s %s:%s" % (file_locations.pantheon_dir, run_dur, run_id, data_dir, 
            flow["protocol"], flow["dst"], file_locations.pantheon_dir)
        os.system("sudo -u %s ssh -i ~/.ssh/id_mininet_rsa %s \"%s\" &" % (username, flow["src"], test_command))

    timeout = 120.0 + max_end + time_offset - time.time()
    all_log_names = ["%s/%s_datalink_run%d.log" % (data_dir, flows[i]["protocol"], run_ids[i]) for i in range(0, len(flows))]
    all_logs_finished = wait_for_all_logs_or_timeout(all_log_names, timeout)
    
    topo.stop_all_link_managers()
    net.stop()

    if not all_logs_finished:
        sys.stderr.write("(PCC Tester) ERROR: test run did not create all expected log files.")

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
    if is_git_repo:
        metadata["Repo"] = git_repo
        metadata["Branch"] = git_branch
        metadata["Checksum"] = git_checksum
    if extra_args is not None:
        metadata["PCC Args"] = []
        for extra_arg in extra_args:
            metadata["PCC Args"].append(extra_arg)
    with open(os.path.join(results_dir, "test_metadata.json"), "w") as f:
        json.dump(metadata, f)
    os.system("rm -rf %s/*" % data_dir)

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

try:
    for test in all_tests:
        run_test(test)
except Exception as e:
    print(e)

if "--is-remote" in sys.argv:
    ssh_utils.cleanup_ssh_connections()
    os.system("sudo killall ssh")
