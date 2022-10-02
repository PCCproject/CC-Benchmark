#!/usr/bin/python3
import sys
import numpy as np
#mpl.style.use("fivethirtyeight")
#from graphing.analysis.results_library import ResultsLibrary, TestResult
#from python_utils.file_locations import results_dir
#from graphing.utils import data_utils
from graphing.utils import basic_graphs
import matplotlib as mpl

mpl.rcParams['ps.useafm'] = True
mpl.rcParams['pdf.use14corefonts'] = True
mpl.rcParams['text.usetex'] = True

"""
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 12}

mpl.rc('font', **font)
"""
import matplotlib.pyplot as plt

param_name = "Bandwidth"
param_unit = "mbps"
params = [1, 2, 4, 8, 16, 32, 64, 128]
#format_string = "bandwidth_sweep.%dmbps"
format_string = "bandwidth_sweep.%dmbps"
flow_name = "flow_1"

def thpt_transform(data):
    return np.multiply(data, 0.001 * np.divide(1.0, np.array(params)))

def lat_transform(data):
    return np.subtract(data, 30.0)

def thpt_score(data):
    return np.multiply(data, 0.1 * np.divide(1.0, np.array(params)))

def lat_score(data):
    #print(data)
    #print([(d - 30.0) / (1000.0 * 1500.0 * 8.0 * 1000.0 / (1000000.0 * p)) for (d, p) in zip(data, params)])
    #print([100.0 - 100.0 * (d - 30.0) / (1500.0 * 8.0 / p) for (d, p) in zip(data, params)])
    return [100.0 - 100.0 * (d - 30.0) / (1500.0 * 8.0 / p) for (d, p) in zip(data, params)]
    #return 100.0 - 100.0 * np.divide(np.subtract(data, 30.0), np.divide(1500.0 * 8.0, np.array(params)))

def loss_score(data):
    return 100.0 * np.subtract(1.0, data)

axes = [
{"data": "Throughput",
 "name": "Link Utilization",
 "func": "semilogx",
 "transform": thpt_transform},
{"data": "Avg Rtt",
 "name": "Self-inflicted Latency (ms)",
 "func": "semilogx",
 "transform": lat_transform}
]

schemes = None
if len(sys.argv) > 1:
    schemes = sys.argv[1].split(",")

"""
basic_graphs.make_sweep_table(format_string, params, flow_name, schemes, thpt_score, lat_score, loss_score)
plt.savefig("bandwidth_scores.pdf", bbox_inches='tight')
plt.cla()
"""

fig, axes = basic_graphs.make_sweep_graph(format_string, params, flow_name,
        schemes, show_spread=False, axes=axes)

fig.legend(loc='center', bbox_to_anchor=(0.65, 0.35))#loc='center right')
axes[0].grid(True)
axes[1].grid(True)
axes[-1].set_xlabel(r"\textbf{%s (%s)}" % (param_name, param_unit))
axes[0].set_ylim((0.0, 1.0))
axes[0].set_ylabel(r"\textbf{Link Utilization}")
axes[1].set_ylabel(r"\textbf{Self-inflicted Latency (ms)}")
#thpt_axis.set_ylim((0.0, 1.0))
plt.savefig("bandwidth_sensitivity.pdf", bbox_inches='tight')
plt.cla()
