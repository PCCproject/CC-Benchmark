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

thpt_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Throughput")
lat_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Avg Rtt")
time_data =  data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Time")
print(thpt_data)
fig, axes = plt.subplots(2)
thpt_axis = axes[0]
lat_axis = axes[1]
for scheme in full_schemes:
    print(scheme)
    thpt_axis.semilogx(time_data[scheme], thpt_data[scheme], label=scheme)
    lat_axis.semilogx(time_data[scheme], lat_data[scheme])

fig.legend()
thpt_axis.set_title("Bandwidth Oscillation")
lat_axis.set_xlabel("Time (ms)")
thpt_axis.set_ylabel("Average Throughput (mbps)")
lat_axis.set_ylabel("Average Latency (ms)")

full_schemes = sorted(results.get_all_schemes_with_tests(params))
thpt_data = {}
fig, axes = plt.subplots(2)
thpt_axis = axes[0]
lat_axis = axes[1]
