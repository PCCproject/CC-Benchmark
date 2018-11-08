#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

results = ResultsLibrary(results_dir)

jitters = [0, 1, 2, 3, 4, 5, 6, 8, 10]
format_string = "jitter_30ms_%dms"

def matching_func(test_result):
    if ("Scheme" not in test_result.metadata):
        print("No metadata for test %s" % test_result.name)
        return False
    if (test_result.metadata["Scheme"] == "default_tcp"):
        return False
    print("Got complete test %s:%s" % (test_result.metadata["Scheme"], test_result.name))
    return True

def get_scheme(test):
    if "Repo" in test.metadata:
        return "%s:%s:%s" % (test.metadata["Repo"], test.metadata["Branch"], test.metadata["Checksum"][-5:])
    return test.metadata["Scheme"]

all_data = {}
summary_data = {}
for j in jitters:
    test_results = results.get_all_results_matching(format_string % j, matching_func)
    this_data = {}
    for test_result in test_results:
        this_test = test_result
        this_test.load()
        scheme = get_scheme(this_test)
        if (scheme not in this_data.keys()):
            this_data[scheme] = {"flows":[]}
        scheme_data = this_data[scheme]
        
        test_events = this_test.flows["flow_1"].data["Events"]
        thpts = [float(event["Throughput"]) / 1000.0 for event in test_events]
        lats = [float(event["Avg Rtt"]) for event in test_events]
        scheme_data["flows"].append(thpts)
    all_data[j] = this_data
    for scheme in this_data.keys():
        if scheme not in summary_data.keys():
            summary_data[scheme] = []

        thpts = []
        for run_data in this_data[scheme]["flows"]:
            thpts.append(np.mean(run_data))
        print("Jitter %d scheme %s thpts %s" % (j, scheme, str(thpts)))
        summary_data[scheme].append(np.mean(thpts))

for scheme in summary_data.keys():
    print("Plotting %s, data %s" % (scheme, str(summary_data[scheme])))
    plt.plot(jitters, summary_data[scheme], label=scheme)

plt.legend()
plt.title("Average Throughput by Jitter")
plt.xlabel("Jitter (ms, from 30ms mean)")
plt.ylabel("Average Throughput (out of 30 mbps)")
plt.show()
