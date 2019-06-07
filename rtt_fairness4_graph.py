#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir
import sys
def smooth_with_linspace(arr, param=100):
    new_arr = []
    for i in range(0, len(arr)-1):
        l = list(np.linspace(arr[i], arr[i+1], param))
        new_arr += l
    return new_arr

def smooth_with_polyfit(x, y):
    orig_len = len(x)

    z = np.polyfit(x, y, 10)
    f = np.poly1d(z)

    x_new = np.linspace(x[0], x[-1], orig_len*1000)
    y_new = f(x_new)

    return (x_new, y_new)

def smooth_time_thpt_lat_with_pfit(time, thpt, lat):
    new_time = []
    new_thpt = []
    new_lat = []

    for i in range(0, len(time)):
        x, y = smooth_with_polyfit(time[i], thpt[i])
        new_time.append(x)
        new_thpt.append(y)
        _, y = smooth_with_polyfit(time[i], lat[i])
        new_lat.append(y)

    return (new_time, new_thpt, new_lat)

if len(sys.argv) != 4:
    print("Usage ./rtt_fairness_graph.py [rtt_1] [rtt2] [rtt3]")
    import os
    os._exit(1)
results = ResultsLibrary(results_dir)

params = (int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
format_string = "rtt_fairness.{}ms_to_{}ms_to_{}ms".format(params[0], params[1], params[2])

full_schemes = results.get_all_schemes_with_tests([format_string])

flow_names = ["flow_1", "flow_2", "flow_3"]

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

# thpt_axes.set_title("Time vs. Throughput")
# thpt_axes.plot(time[0], thpt[0], label="{}ms flow".format(params[0]))
# thpt_axes.plot(time[1], thpt[1], label="{}ms flow".format(params[1]))
# thpt_axes.plot(time[2], thpt[2], label="{}ms flow".format(params[2]))
#
# lat_axes.set_title("Time vs. Latency")
# lat_axes.plot(time[0], lat[0])
# lat_axes.plot(time[1], lat[1])
# lat_axes.plot(time[2], lat[2])

new_t, new_thpt, new_lat = smooth_time_thpt_lat_with_pfit(time, thpt, lat)

thpt_axes.set_title("Time vs. Throughput")
thpt_axes.plot(new_t[0], new_thpt[0], label="{}ms flow".format(params[0]))
thpt_axes.plot(new_t[1], new_thpt[1], label="{}ms flow".format(params[1]))
thpt_axes.plot(new_t[2], new_thpt[2], label="{}ms flow".format(params[2]))

lat_axes.set_title("Time vs. Latency")
lat_axes.plot(new_t[0], new_lat[0])
lat_axes.plot(new_t[1], new_lat[1])
lat_axes.plot(new_t[2], new_lat[2])

fig.legend()

plt.savefig("{}ms_to_{}ms_to_{}ms_rtt.png".format(params[0], params[1], params[2]))
