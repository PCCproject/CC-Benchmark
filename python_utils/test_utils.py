from python_utils import file_locations
import json
import os
import numpy as np
import json
import time
import signal

SUPPORTED_PANTHEON_SCHEMES = [
    "copa",
    "vivace_latency",
    "default_tcp",
    "pcc",
    "bbr",
    "taova",
    "vegas",
    "sprout",
    "ledbat"
]

MANNUALLY_MAMANGED_VM_IPS = [
    "192.168.122.22"
]

def clear_testfile_and_exit(sig=None, frame=None):
    with open(file_locations.local_test_running_dir, 'w') as f:
        f.write("false\r\n")
    if sig == signal.SIGINT:
        os._exit(0)

def get_wait_time_from_VM():
    local = None
    remote = None

    with open(file_locations.remote_test_running_dir) as f:
        remote = f.read()
    if remote.startswith("true"):
        remote = remote.split("\r\n")[0].split(" ")
        print(remote)
        time_elasped = time.time() - float(remote[2])
        time_remain = float(remote[1]) - time_elasped
        return time_remain

    with open(file_locations.local_test_running_dir) as f:
        local = f.read()

    if local.startswith("true"):
        local = local.split("\r\n")[0].split(" ")
        print(local)
        time_elasped = time.time() - float(local[2])
        time_remain = float(local[1]) - time_elasped
        return time_remain

    return 0

def get_test_dur(test):
    test_file = file_locations.tests_dir + "/" + test + ".json"
    max_dur = 0
    try:
        with open(test_file, 'r') as f:
            meta = json.loads(f.read())
            for flow in meta['Flows']:
                curr_flow = flow['dur']
                if curr_flow > max_dur:
                    max_dur = curr_flow
    except Exception as e:
        print("filenotfound")
        print(e)

    return max_dur

def get_total_test_time(tests, number_of_vms):
    distributed_time = np.zeros(number_of_vms)
    for test in tests:
        min_idx = np.argmin(distributed_time)
        test_dur = get_test_dur(test)
        distributed_time[min_idx] += (test_dur + 60) # add 60 second for timeout between test and log conversion/merge time

    return np.max(distributed_time)

def get_host_name():
    import socket
    return socket.gethostname()

def occupy_remote_vm(tests):
    pass

def occupy_local_vm(tests):
    pass

def free_remote_vm():
    with open(file_locations.remote_test_running_dir, 'w') as f:
        f.write("false")

def free_local_vm():
    with open(file_locations.local_test_running_dir, 'w') as f:
        f.write("false")

def get_remaining_test_time():
    with open(file_locations.remote_test_running_dir, 'r') as f:
        remote = f.read().rstrip()
        if 'true' in remote:
            info = remote.split(' ')
            start_time = float(info[1])
            total_time = float(info[2])
            elapsed_time = time.time() - start_time
            return total_time - elapsed_time + 30

    with open(file_locations.local_test_running_dir, 'r') as f:
        local = f.read().rstrip()
        if 'true' in remote:
            info = local.split(' ')
            start_time = float(info[1])
            total_time = float(info[2])
            elapsed_time = time.time() - start_time
            return total_time - elapsed_time + 30

    # tests are done
    return -1

def check_idle():
    with open(file_locations.local_test_running_dir, 'r') as f:
        local = f.read().rstrip()
        if 'false' not in local:
            return False

    with open(file_locations.remote_test_running_dir, 'r') as f:
        remote = f.read().rstrip()
        if 'false' not in remote:
            return False

    return True

##
#  Takes a topology name and reads the corresponding topology json into a dict.
##
def read_topology_to_dict(topology_name):
    topo_file = os.path.join(file_locations.topos_dir, topology_name + ".json")
    topo_json = None
    with open(topo_file) as f:
        topo_json = json.load(f)
    return topo_json

##
#   Reads a test or test list file and returns a list of filenames from which tests should be
#   loaded.
##
def read_test_list_to_list(test_list):
    test_file = os.path.join(file_locations.tests_dir, test_list) + ".json"
    test_json = None
    with open(test_file) as f:
        test_json = json.load(f)

    # If the filename passed in was already just a single test, then return a list with it's name
    if not ("Tests" in test_json.keys()):
        return [test_list]

    tests = []

    # The filename passed in is for a test list, so return the list of tests
    for test_name in test_json["Tests"]:
        tests += read_test_list_to_list(test_name)

    return tests

##
#   Takes a test name and reads the corresponding test json into a dict.
##
def read_test_to_dict(test_name):
    test_file = os.path.join(file_locations.tests_dir, test_name) + ".json"
    test_json = None
    with open(test_file) as f:
        test_json = json.load(f)
    return test_json
