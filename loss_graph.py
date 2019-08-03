#!/usr/bin/python3
import sys
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from graphing.utils import data_utils
from python_utils.file_locations import results_dir
from graphing.utils import nice_names
from graphing.utils import basic_graphs
mpl.rcParams['ps.useafm'] = True
mpl.rcParams['pdf.use14corefonts'] = True
mpl.rcParams['text.usetex'] = True

"""
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 12}

mpl.rc('font', **font)
"""

#mpl.style.use("fivethirtyeight")

results = ResultsLibrary(results_dir)

param_name = "Loss Probability"
#params = ["0.0001", "0.001", "0.005", "0.01", "0.015", "0.02", "0.025", "0.03", "0.04", "0.05",
#    "0.06", "0.08", "0.1", "0.15", "0.20"]
params = ["0.0001", "0.001", "0.005", "0.01", "0.015", "0.02", "0.025", "0.03", "0.04", "0.05",
    "0.06", "0.08"]
format_string = "simple_%sloss"
flow_name = "flow_1"

def thpt_transform(data):
    return np.multiply(data, 0.001 * np.divide(1.0, 32.0))

def lat_transform(data):
    return np.subtract(data, 30.0)

def thpt_score(data):
    return np.multiply(data, 0.1 * np.divide(1.0, 32.0))

def lat_score(data):
    return [100.0 - 100.0 * (d - 30.0) / (1500.0 * 8.0 / 32.0) for d in data]

def loss_score(data):
    return [100.0 - 100.0 * (d - float(p)) / (1.0 - float(p)) for (d, p) in zip(data, params)]

axes = [
{"data": "Throughput",
 "name": "Link Utilization",
 "func": "plot",
 "transform": thpt_transform},
{"data": "Avg Rtt",
 "name": "Self-inflicted Latency (ms)",
 "func": "plot",
 "transform": lat_transform}#,
#{"data": "Loss Rate",
# "name": "Loss Rate",
# "func": "semilogx",
# "transform": None}
]

schemes = None
if len(sys.argv) > 1:
    schemes = sys.argv[1].split(",")

"""
basic_graphs.make_sweep_table(format_string, params, flow_name, schemes, thpt_score, lat_score, loss_score)
plt.savefig("loss_scores.pdf", bbox_inches='tight')
plt.cla()
"""

fig, axes = basic_graphs.make_sweep_graph(format_string, params, flow_name,
        schemes, show_spread=False, axes=axes)

[axis.grid(True) for axis in axes]
fig.legend(loc='center', bbox_to_anchor=(0.65, 0.30))#loc='center right')
#thpt_axis.set_title("%s Test Performance" % param_name)
axes[-1].set_xlabel(r"\textbf{Loss Probability}")
axes[0].set_ylabel(r"\textbf{Link Utilization}")
axes[1].set_ylabel(r"\textbf{Self-inflicted Latency (ms)}")
#axes[2].set_ylabel("Loss Rate")
plt.savefig("loss_sensitivity.pdf", bbox_inches='tight')
plt.cla()
