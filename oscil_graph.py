#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir
from graphing.utils import data_utils

results = ResultsLibrary(results_dir)

param_name = "Bandwidth"
param_unit = "mbps"
#params = [1, 2, 4, 8, 16, 32, 64, 128]
params = ["simple_10_to_20mbps_oscillation"]
#params = ["latency_test_128ms"]
#format_string = "simple_%dmbps"
format_string = ""
flow_name = "flow_1"


full_schemes = sorted(results.get_all_schemes_with_tests(params))
fig, axes = plt.subplots(2)
thpt_axis = axes[0]
lat_axis = axes[1]
thpt = {}
lat = {}
time = {}
for scheme in full_schemes:
    print(scheme)
    filter_func = lambda test_result : test_result.get_scheme_name() == scheme
    thpt_data = []
    lat_data = []
    time_data = []
    for p in params:
        scheme_results = results.get_all_results_matching(p, filter_func=filter_func)
        print(len(scheme_results))
        [scheme_result.load() for scheme_result in scheme_results]
        thpt_data.append([sr.flows[flow_name].get_event_data("Throughput") for sr in scheme_results])
        time_data.append([sr.flows[flow_name].get_event_data("Time") for sr in scheme_results])
        #time_data = [(t - time_data[scheme][0]) / 1000.0 for t in time_data[scheme]]
        print(time_data[scheme])
        #time = [sr.flows[flow_name].get_statistic("Time", "Mean") for sr in scheme_results]
        lat_data[scheme] = [sr.flows[flow_name].get_event_data("Avg Rtt") for sr in scheme_results]
    thpt_data[scheme] = thpt
    print(thpt_data[scheme])

for scheme in full_schemes:
    thpt_axis.plot(list(range(len(thpt_data[scheme]))), thpt_data[scheme], label=scheme)
    lat_axis.plot(list(range(len(lat_data[scheme]))), lat_data[scheme])

fig.legend()
thpt_axis.set_title("%s Test Performance" % param_name)
lat_axis.set_xlabel("%s (%s)" % (param_name, param_unit))
thpt_axis.set_ylabel("Average Throughput (mbps)")
lat_axis.set_ylabel("Average Latency (ms)")
plt.show()
