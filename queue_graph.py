#!/usr/bin/python3
import sys
import numpy as np
from graphing.utils import basic_graphs
import matplotlib.pyplot as plt

param_name = "Queue Size"
param_unit = "KB"
params = [1, 2, 3, 4, 5, 10, 100, 1000, 10000]
format_string = "queue_sweep.%dpkt"
flow_name = "flow_1"

def thpt_transform(data):
    return np.multiply(data, 0.001 * (1.0 / 30.0))

def lat_transform(data):
    return np.subtract(data, 30.0)

def thpt_score(data):
    return np.multiply(data, 0.1 * np.divide(1.0, 32.0))

def lat_score(data):
    #print(data)
    #print([(d - 30.0) / (1000.0 * 1500.0 * 8.0 * 1000.0 / (1000000.0 * p)) for (d, p) in zip(data, params)])
    #print([100.0 - 100.0 * (d - 30.0) / (1500.0 * 8.0 / p) for (d, p) in zip(data, params)])
    return [100.0 - 100.0 * (d - 30.0) / (1500.0 * 8.0 * p / 32000.0) for (d, p) in zip(data, params)]
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

basic_graphs.make_sweep_table(format_string, params, flow_name, schemes, thpt_score, lat_score, loss_score)
plt.savefig("queue_scores.pdf", bbox_inches='tight')
plt.cla()


fig, axes = basic_graphs.make_sweep_graph(format_string, params, flow_name,
        schemes, show_spread=True, axes=axes)

fig.legend(loc="center", bbox_to_anchor=(0.65, 0.65))
axes[-1].set_xlabel("%s (%s)" % (param_name, param_unit))
plt.savefig("queue_sensitivity.pdf")
