#!/usr/bin/python3
import sys
import random
import numpy as np
from numpy import ma
import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

##
#   First, just define a few variables looking at which test, scheme and flow we care about"
##
test_name = "simple_oscil_buf_20_bw_40_no_loss"
#test_name = "simple_oscil_buf_5_bw_40_no_loss"
scheme_names = ["default_tcp", "pcc_test_scheme"]
#scheme_names = ["default_tcp"]
flow_name = "flow_1"

##
#   Next, load in the results library.
##
results = ResultsLibrary(results_dir)


def get_plottable_scheme_data(results_lib, scheme_name):
    ##
    #   We only want to use test results from one scheme, so we create a filter_func that returns true
    #   for just those tests.
    ##
    filter_func = lambda test_result: test_result.get_scheme_name() == scheme_name
    scheme_results = results.get_all_results_matching(test_name, filter_func=filter_func)

    ##
    #   Now, we want to get the flow data from our tests. Since we only want to show one flow, I just
    #   picked the first result we have (scheme_results[0]). You could write a few if-statements to
    #   pick whichever result you want to graph.
    ##
    single_result = scheme_results[0]
    single_result.load()
    flow_result = single_result.flows[flow_name]

    ##
    #   We've got at FlowTrace object, which lets us get all the named event data. You can see which
    #   names you can use by looking in the .json files in your results directories. We want
    #   "Time" for the x-axis and "Throughput" for the y-axis.
    ##
    time_data = flow_result.get_event_data("Time",include_setup=True)

    # Here, I'm just re-scaling time. It was in ms and had an offset. By subtracting the first point
    # and dividing by 1000.0, I've made it into seconds since test start.
    time_data = [(t - time_data[0]) / 1000.0 for t in time_data]

    thpt_data = flow_result.get_event_data("Throughput",include_setup=True)
    #print("setup_index is %d, time %f" % (flow_result.setup_end, time_data[flow_result.setup_end - 1]))
    setup_end = time_data[flow_result.setup_end - 1]
    print("setup end? ",  setup_end)
    # Add include_setup=True to get full info
    # Throughput data is in kbps, but mbps is more understandable, so I just divide each sample by 1000.0
    thpt_data = [t / 1000.0 for t in thpt_data]

    lat_data = flow_result.get_event_data("Loss Rate",include_setup=True)

    return time_data, thpt_data, lat_data, setup_end


def truncate_data_to_time(truncate_start, truncate_end, time_data, other_data):
    trunc_index = len(time_data)
    trunc_start_index = next(i for i, v in enumerate(time_data) if v > truncate_start)
    print("entering? ", time_data[-1])
    if time_data[-1] > truncate_end:
        print("Getting trunc index")
        # trunc_indexfilter(lambda x: x>.7, seq)[0]

        trunc_index = next(i for i, v in enumerate(time_data) if v > truncate_end)
        print("trunc_start_index is %d, time %f" % (trunc_start_index, time_data[trunc_start_index - 1]))
        print("trunc_index is %d, time %f" % (trunc_index, time_data[trunc_index - 1]))
        print("prev time %f" % (time_data[trunc_index - 2]))
    return time_data[:trunc_index - trunc_start_index], other_data[trunc_start_index:trunc_index]


# Below is just some standard matplotlib code. You won't be able to "show" the graph with what I did on
# line 6, but if you delete line 6, you can change the "savefig()" to "show()".
# fig, axes = plt.subplots(2)
nice_names = {
    "vivace_latency": "PCC-Vivace",
    "default_tcp": "TCP CUBIC",
    "mlp_scale_free": "Aurora",
    "pcc_test_scheme": "RL-based",
    "copa": "Copa",
    "bbr": "BBR"
}

fig, ax = plt.subplots()
plt.xlabel("Time (s)")
plt.ylabel("Throughput (mbps)")

# plt.rcParams["figure.figsize"] = (10,3)
plt = plt.figure(figsize=(8, 5))
setup_ends = {}
truncate_end = 30.0

for scheme_name in scheme_names:
    print(scheme_name)
    time_data, thpt_data, lat_data, setup_ends[scheme_name] = get_plottable_scheme_data(results, scheme_name)

truncate_start = max(setup_ends.values())
print("truncate start? %d" % truncate_start)
for scheme_name in scheme_names:
    print(scheme_name)
    time_data, thpt_data, lat_data, setup_ends[scheme_name] = get_plottable_scheme_data(results, scheme_name)
    time_data, thpt_data = truncate_data_to_time(truncate_start, truncate_end, time_data, thpt_data)
    ax.plot(time_data, thpt_data, label=nice_names[scheme_name])
#line_x = [0,5,5.0000000000001,10,10.0000000000001,15, 15.0000000000001,20, 20.0000000000001,25]
setup_end = min(setup_ends.values())
# print(5 - setup_end)
if 5 - setup_end < 0:
     line_x = [0, (10 - setup_end), (10 - setup_end)+ 0.0000000000001,(15 - setup_end), (15 - setup_end) + 0.0000000000001,(20 - setup_end), (20-setup_end) + 0.0000000000001, 25 - setup_end, (25 - setup_end) + 0.0000000000001,truncate_end]
else:
      line_x = [0, setup_end, setup_end, 5 + setup_end, 5 + setup_end ,10 + setup_end, 10 + setup_end, 15 + setup_end, 15 + setup_end,20 + setup_end, 20 + setup_end, truncate_end - truncate_start]

line_y = [20,20,40,40,20,20,40,40,20,20,40,40]
#ax.axhline(y = 40, color='black', linestyle='--', label="Optimum")
ax.plot(line_x, line_y, color='black', linestyle='--', label="Optimum")
fig.legend(loc='center', bbox_to_anchor=(0.55,-0.065, 0.5, 0.5))
# plt.xlabel("Time (s)")
# plt.ylabel("Sending rate (mbps)")
fig.savefig("my_graph.png")
