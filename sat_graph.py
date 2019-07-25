#!/usr/bin/python3
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.style.use("fivethirtyeight")
from graphing.analysis.results_library import ResultsLibrary, TestResult
from graphing.utils import data_utils
from python_utils.file_locations import results_dir

results = ResultsLibrary(results_dir)

param_name = "Satellite Queue Size"
param_unit = "packets"
params = [2, 8, 80, 600, 1000]
format_string = "nsdi_satellite_%dpkt"
flow_name = "flow_1"

full_schemes = results.get_all_schemes_with_tests([format_string % p for p in params])
if len(sys.argv) > 1:
    used_schemes = sys.argv[1].split(" ")
    full_schemes = list(set(full_schemes) & set(used_schemes))
thpt_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Throughput")
lat_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name, params,
        format_string, "Avg Rtt")

fig, axes = plt.subplots(2)
thpt_axis = axes[0]
lat_axis = axes[1]
for scheme in full_schemes:
    thpt_axis.semilogx(params, thpt_data[scheme], label=scheme)
    lat_axis.semilogx(params, lat_data[scheme])

fig.legend()
thpt_axis.set_title("%s Test Performance" % param_name)
lat_axis.set_xlabel("%s (%s)" % (param_name, param_unit))
thpt_axis.set_ylabel("Average Throughput (mbps)")
lat_axis.set_ylabel("Average Latency (ms)")
plt.show()
