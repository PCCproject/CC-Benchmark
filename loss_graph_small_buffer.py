#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from graphing.utils import data_utils
from python_utils.file_locations import results_dir

results = ResultsLibrary(results_dir)

param_name = "Loss Rate"
param_unit = "proportion"
params = ["0.0001", "0.001", "0.005", "0.01", "0.015", "0.02", "0.025", "0.03", "0.04", "0.05"]
format_string = "simple_%sloss_small_buffer"
flow_name = "flow_1"

full_schemes = results.get_all_schemes_with_tests([format_string % p for p in params])
thpt_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Throughput")
lat_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Avg Rtt", statistic="Ack-weighted Mean")
loss_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Loss Rate", statistic="Send-weighted Mean")

fig, axes = plt.subplots(3)
thpt_axis = axes[0]
lat_axis = axes[1]
loss_axis = axes[2]
for scheme in full_schemes:
    thpt_axis.plot([float(p) for p in params], thpt_data[scheme], label=scheme)
    lat_axis.plot([float(p) for p in params], lat_data[scheme])
    loss_axis.plot([float(p) for p in params], loss_data[scheme])

fig.legend()
thpt_axis.set_title("%s Test Performance" % param_name)
lat_axis.set_xlabel("%s (%s)" % (param_name, param_unit))

thpt_axis.set_ylabel("Average Throughput (mbps)")
lat_axis.set_ylabel("Average Latency (ms)")
loss_axis.set_ylabel("Average Loss Rate")

plt.show()
