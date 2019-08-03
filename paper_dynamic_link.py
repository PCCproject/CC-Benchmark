#!/usr/bin/python3
import sys
import random
import numpy as np
import matplotlib as mpl
mpl.use("Agg")

mpl.rcParams['ps.useafm'] = True
mpl.rcParams['pdf.use14corefonts'] = True
mpl.rcParams['text.usetex'] = True

import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir
from graphing.utils import nice_names

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

param_name = "Loss Rate"
param_unit = "proportion"
test_name = "custard_variable_link"
flow_name = "flow_1"


full_schemes = sorted(results.get_all_schemes_with_tests([test_name]))
full_schemes = ["default_tcp", "icml_paper_final", "vivace_latency", "bbr", "copa", "taova"]
if len(sys.argv) > 1:
    used_schemes = sys.argv[1].split(",")
    full_schemes = list(set(full_schemes) & set(used_schemes))
markers = {}
for scheme in full_schemes:
    markers[scheme] = get_random_marker()

plt.gca().invert_xaxis()
plt.grid(True)
fig, ax = plt.subplots(1)
ax.set_axisbelow(True)
ax.grid(True)
for scheme in full_schemes:
    filter_func = lambda test_result : test_result.get_scheme_name() == scheme
    thpt_data = []
    lat_data = []
    scheme_results = results.get_all_results_matching(test_name, filter_func=filter_func)
    [scheme_result.load() for scheme_result in scheme_results]
    thpt_data = [sr.flows["flow_1"].get_statistic("Throughput", "Mean") / 1000.0 for sr in scheme_results]
    lat_data = [sr.flows["flow_1"].get_statistic("Avg Rtt", "Ack-weighted Mean") for sr in scheme_results]
    print("Scheme %s has %d runs" % (scheme, len(thpt_data)))
    print("\tThroughput: %f" % np.mean(thpt_data))
    print("\tLatency: %f" % np.mean(lat_data))
    ax.scatter(lat_data, thpt_data, label=nice_names.get_nice_name(scheme), marker=markers[scheme])#, edgecolor='black', linewidths=1)

ax.scatter([30.0], [24.0], label="Optimal", marker='*', color='black', edgecolor='black', linewidths=1, s=120)

ax.legend()
ax.set_xlabel("Average Latency (ms)")
ax.set_ylabel("Average Throughput (mbps)")
#plt.title("%s Throughput-Latency Tradeoff" % (test_name))
fig.savefig("dynamic_link.pdf")
