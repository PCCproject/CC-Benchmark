#!/usr/bin/python3
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

results = ResultsLibrary(results_dir)

def matching_func(test_result):
    print("Checking test result %s" % test_result.name)
    return test_result.metadata["Scheme"] == sys.argv[1]

test_result = results.get_all_results_matching("delayed_fairness", matching_func)[0]
test_result.load()

scheme = test_result.metadata["Scheme"]
tcp_flow_times = [float(event["Time"]) / 1000.0 for event in test_result.flows["flow_1"].data["Events"]]
tcp_flow_thpts = [float(event["Throughput"]) / 1000.0 for event in test_result.flows["flow_1"].data["Events"]]
plt.plot(tcp_flow_times, savgol_filter(tcp_flow_thpts, 13, 1), label="%s flow #1" % scheme, linestyle=':')

other_flow_times = [float(event["Time"]) / 1000.0 for event in test_result.flows["flow_2"].data["Events"]]
other_flow_thpts = [float(event["Throughput"]) / 1000.0 for event in test_result.flows["flow_2"].data["Events"]]
plt.plot(other_flow_times, savgol_filter(other_flow_thpts, 13, 1), label="%s flow #2" % scheme)

plt.legend()
plt.title("Delayed Competition")
plt.xlabel("Time (s)")
plt.ylabel("Throughput (out of 30 Mbps)")
plt.show()
