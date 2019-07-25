#!/usr/bin/python3
import sys
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

results = ResultsLibrary(results_dir)

def matching_func(test_result):
    print("Checking test result %s" % test_result.name)
    return test_result.metadata["Scheme"] == sys.argv[1]

test_result = results.get_all_results_matching("oscillating_competition_10s", matching_func)#[0]
print(test_result)
test_result.load()
print(test_result.flows)

time_offset = float(test_result.flows["main_flow"].data["Events"][0]["Time"])

scheme = test_result.metadata["Scheme"]
for flow_name in test_result.flows.keys():
    times = [(float(event["Time"]) - time_offset) / 1000.0 for event in test_result.flows[flow_name].data["Events"]]
    thpts = [float(event["Throughput"]) / 1000.0 for event in test_result.flows[flow_name].data["Events"]]
    plt.plot(times, savgol_filter(thpts, 13, 1))
    #plt.plot(times, thpts)

plt.legend()
plt.title("Oscillating Competition")
plt.xlabel("Time (s)")
plt.ylabel("Throughput (out of 30 Mbps)")
plt.savefig("oc_result.png")
