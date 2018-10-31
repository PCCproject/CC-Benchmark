import json
import os

class FlowTrace():
    def __init__(self, filename):
        self.data = {}
        with open(filename) as f:
            self.data = json.load(f)

class TestResult():
    def __init__(self, test_name, dir_name):
        self.name = test_name
        self.dir_name = dir_name
        self.flows = {}
        self.metadata = {}
        self.loaded = False
        self.load_metadata()

    def load_metadata(self):
        with open(os.path.join(self.dir_name, "test_metadata.json")) as f:
            self.metadata = json.load(f)

    def is_loaded(self):
        return self.loaded

    def load(self):
        self.loaded = True
        filenames = os.listdir(self.dir_name)
        for filename in filenames:
            if filename == "test_metadata.json":
                continue
            elif ".json" in filename:
                flow_name = filename.split('.')[1]
                print("Loading flow %s" % flow_name)
                self.flows[flow_name] = FlowTrace(os.path.join(self.dir_name, filename))

class ResultsLibrary():
    def __init__(self, dir_name):
        self.dir_name = dir_name

        # Test results are entered in the dictionary by name, then a list of all results for the
        # test of that name.
        self.test_results = {}
        self.load_all_metadata()

    def get_all_results_matching(self, test_name, filter_func):
        returned_results = []
        for test_result in self.test_results[test_name]:
            if filter_func(test_result):
                returned_results.append(test_result)
        return returned_results

    def load_all_metadata_for_test(self, test_name):
        this_test_dir = os.path.join(self.dir_name, test_name)
        tests = []
        for test_time_dir in os.listdir(this_test_dir):
            tests.append(TestResult(test_name, os.path.join(this_test_dir, test_time_dir)))
        self.test_results[test_name] = tests

    def load_all_metadata(self):
        all_test_dirs = os.listdir(self.dir_name)
        for test_dir in all_test_dirs:
            self.load_all_metadata_for_test(test_dir)

