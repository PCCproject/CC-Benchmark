#!/usr/bin/python3
import sys
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
mpl.style.use("fivethirtyeight")
from graphing.analysis.results_library import ResultsLibrary, TestResult
from graphing.utils import data_utils
from python_utils.file_locations import results_dir
from graphing.utils import basic_graphs

results = ResultsLibrary(results_dir)

param_name = "Jitter"
param_unit = "ms from 30ms"
params = [0, 1, 2, 3, 4, 5, 6, 8, 10]
format_string = "jitter_sweep.30ms_%dms"
flow_name = "flow_1"

def thpt_transform(data):
    return np.multiply(data, 0.001 * np.divide(1.0, 30))

def lat_transform(data):
    return np.subtract(data, params)

def thpt_score(data):
    return np.multiply(data, 0.1 * np.divide(1.0, 32.0))

def lat_score(data):
    return [100.0 - 100.0 * (d - 30) / (1500.0 * 8.0 / 32.0) for d in data]

def loss_score(data):
    return 100.0 * np.subtract(1.0, data)

axes = [
{"data": "Throughput",
 "name": "Link Utilization",
 "func": "plot",
 "transform": thpt_transform},
{"data": "Avg Rtt",
 "name": "Self-inflicted Latency (ms)",
 "func": "plot",
 "transform": lat_transform}
]

schemes = None
if len(sys.argv) > 1:
    schemes = sys.argv[1].split(",")

basic_graphs.make_sweep_table(format_string, params, flow_name, schemes, thpt_score, lat_score, loss_score)
plt.savefig("jitter_scores.pdf", bbox_inches='tight')
plt.cla()

fig, axes = basic_graphs.make_sweep_graph(format_string, params, flow_name,
        schemes, show_spread=True, axes=axes)

fig.legend(loc='center', bbox_to_anchor=(0.65, 0.35))#loc='center right')
axes[0].grid(True)
axes[1].grid(True)
axes[-1].set_xlabel("%s (%s)" % (param_name, param_unit))
plt.savefig("jitter_sensitivity.pdf", bbox_inches='tight')
