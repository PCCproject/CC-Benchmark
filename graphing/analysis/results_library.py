import json
import os
from graphing.analysis.flow_trace import FlowTrace

class TestResult():
    def __init__(self, test_name, dir_name):
        self.name = test_name
        self.dir_name = dir_name
        self.flows = {}
        self.metadata = None
        self.loaded = False
        self.load_metadata()

    def load_metadata(self):
        try:
            with open(os.path.join(self.dir_name, "test_metadata.json")) as f:
                self.metadata = json.load(f)
        except FileNotFoundError as e:
            print("Warning: Failed to load metadata for %s" % self.dir_name)

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
                self.flows[flow_name] = FlowTrace(os.path.join(self.dir_name, filename))

    def get_scheme_name(self):
        if "Repo" in self.metadata:
            return "%s:%s:%s" % (self.metadata["Repo"], self.metadata["Branch"], self.metadata["Checksum"][-5:])
        return self.metadata["Scheme"]

    def has_metadata(self):
        return self.metadata is not None

    def delete_from_disk(self):
        print("Deleting test from %s" % self.dir_name)
        os.system("rm -rf %s" % self.dir_name)

class ResultsLibrary():
    def __init__(self, dir_name):
        self.dir_name = dir_name

        # Test results are entered in the dictionary by name, then a list of all results for the
        # test of that name.
        self.test_results = {}
        self.load_all_metadata()

    def get_all_results_matching(self, test_name, filter_func=None):
        returned_results = []
        for test_result in self.test_results[test_name]:
            if test_result.has_metadata() and (filter_func is None or filter_func(test_result)):
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

    def get_all_schemes_with_test(self, test_name, num_replicas):
        results = self.get_all_results_matching(test_name)
        schemes = []
        for result in results:
            scheme = result.get_scheme_name()
            if scheme not in schemes:
                schemes.append(scheme)
        return schemes

    def get_all_schemes_with_tests(self, list_of_tests, num_replicas=1):
        schemes = self.get_all_schemes_with_test(list_of_tests[0], num_replicas)
        if len(list_of_tests) == 1:
            return schemes

        for test_name in list_of_tests[1:]:
            new_schemes = self.get_all_schemes_with_test(test_name, num_replicas)
            print(schemes)
            print(new_schemes)
            schemes_with_both = set(schemes) & set(new_schemes)
            schemes = list(schemes_with_both)

        return schemes

    def delete_no_metadata_tests(self):
        for result_list in self.test_results.values():
            for test_result in result_list:
                if not test_result.has_metadata():
                    test_result.delete_from_disk()
