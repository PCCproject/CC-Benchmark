from python_utils import file_locations
import json
import os

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
