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

test_result = results.get_all_results_matching("tcp_fairness", matching_func)[0]
test_result.load()

tcp_flow_times = [float(event["Time"]) / 1000.0 for event in test_result.flows["tcp_flow"].data["Events"]]
tcp_flow_thpts = [float(event["Avg Rtt"]) / 1000.0 for event in test_result.flows["tcp_flow"].data["Events"]]
plt.plot(tcp_flow_times, savgol_filter(tcp_flow_thpts, 13, 1), label="TCP Flow", linestyle=':')

other_flow_times = [float(event["Time"]) / 1000.0 for event in test_result.flows["flow_1"].data["Events"]]
other_flow_thpts = [float(event["Avg Rtt"]) / 1000.0 for event in test_result.flows["flow_1"].data["Events"]]
plt.plot(other_flow_times, savgol_filter(other_flow_thpts, 13, 1), label= test_result.metadata["Scheme"])

plt.legend()
plt.title("Competing with TCP")
plt.xlabel("Time (s)")
plt.ylabel("Throughput (out of 30 Mbps)")
plt.show()
