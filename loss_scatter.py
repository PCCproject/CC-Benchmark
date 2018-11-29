#!/usr/bin/python3
import random
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

print(plt.style.available)
mpl.style.use("fivethirtyeight")

results = ResultsLibrary(results_dir)
avail_markers = mpl.markers.MarkerStyle.markers.copy()
del avail_markers[',']
del avail_markers['.']
del avail_markers[None]
del avail_markers['None']
del avail_markers[' ']
del avail_markers['']
del avail_markers['x']
del avail_markers['_']
del avail_markers['+']
for i in range(0, 12):
    del avail_markers[i]
    if str(i) in avail_markers.keys():
        del avail_markers[str(i)]
avail_markers = list(avail_markers.keys())

_cur_marker = 0
def get_random_marker():
    global _cur_marker
    marker = avail_markers[_cur_marker]
    _cur_marker += 1
    if _cur_marker >= len(avail_markers):
        _cur_marker = 0
    return mpl.markers.MarkerStyle(marker=marker)

#param_name = "Bandwidth"
#param_unit = "mbps"
#params = [1, 2, 4, 8, 16, 32, 64, 128]
#format_string = "simple_%dmbps"

param_name = "Loss Rate"
param_unit = "proportion"
params = ["0.0001", "0.001", "0.005", "0.01", "0.015", "0.02", "0.025", "0.03", "0.04", "0.05",
    "0.06", "0.08", "0.1", "0.15", "0.20"]
format_string = "simple_%sloss"
flow_name = "flow_1"

full_schemes = sorted(results.get_all_schemes_with_tests([format_string % p for p in params]))
markers = {}
for scheme in full_schemes:
    markers[scheme] = get_random_marker()

for p in params:
    for scheme in full_schemes:
        filter_func = lambda test_result : test_result.get_scheme_name() == scheme
        thpt_data = []
        lat_data = []
        scheme_results = results.get_all_results_matching(format_string % p, filter_func=filter_func)
        [scheme_result.load() for scheme_result in scheme_results]
        thpt_data = [sr.flows["flow_1"].get_statistic("Throughput", "Mean") / 1000.0 for sr in scheme_results]
        lat_data = [sr.flows["flow_1"].get_statistic("Avg Rtt", "Mean") for sr in scheme_results]
        plt.scatter(lat_data, thpt_data, label=scheme, marker=markers[scheme])#, edgecolor='black', linewidths=1)
    plt.legend()
    plt.title("%s Throughput-Latency Tradeoff" % (format_string % p))
    plt.show()

