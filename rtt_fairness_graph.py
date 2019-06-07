#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir
import sys
if len(sys.argv) != 3:
    print("Usage ./rtt_fairness_graph.py [rtt_1] [rtt2]")
    import os
    os._exit(1)
results = ResultsLibrary(results_dir)

params = (int(sys.argv[1]), int(sys.argv[2]))
format_string = "rtt_fairness.{}ms_to_{}ms".format(params[0], params[1])

full_schemes = results.get_all_schemes_with_tests([format_string])

flow_names = ["flow_1", "flow_2"]

fig, axes = plt.subplots(2)
thpt_axes = axes[0]
lat_axes = axes[1]

thpt = []
lat = []
time = []

for scheme in full_schemes:
    filter_func = lambda test_result : test_result.get_scheme_name() == scheme

    scheme_results = results.get_all_results_matching(format_string\
                    .format(params[0], params[1]), filter_func=filter_func)

    for scheme_result in scheme_results:
        scheme_result.load()

    for flow_name in flow_names:
        # Normalize time
        time_tmp = np.array([scheme_result.flows[flow_name].get_event_data("Time") for scheme_result in scheme_results][0])
        time_tmp -= time_tmp[0]

        lat.append([scheme_result.flows[flow_name].get_event_data("Avg Rtt") for scheme_result in scheme_results][0])
        thpt.append([scheme_result.flows[flow_name].get_event_data("Throughput") for scheme_result in scheme_results][0])
        time.append(time_tmp)

fig.set_size_inches(10.0, 13.0)



thpt_axes.set_title("Time vs. Throughput")
thpt_axes.plot(time[0], thpt[0], label="{}ms flow".format(params[0]))
thpt_axes.plot(time[1], thpt[1], label="{}ms flow".format(params[1]))

lat_axes.set_title("Time vs. Latency")
lat_axes.plot(time[0], lat[0])
lat_axes.plot(time[1], lat[1])

fig.legend()
plt.savefig("{}ms_to_{}ms_rtt.png".format(params[0], params[1]))
