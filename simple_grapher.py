#!/usr/bin/python3
import sys
import random
import numpy as np
import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

##
#   First, just define a few variables looking at which test, scheme and flow we care about"
##
params = ["simple_10_to_20mbps_oscillation"]
#params =["latency_test_256ms"]
test_name = params[0]
#scheme_name = "pcc_test_scheme"
flow_name = "flow_1"

##
#   Next, load in the results library.
##
results = ResultsLibrary(results_dir)
scheme_names = sorted(results.get_all_schemes_with_tests(params))

def get_plottable_scheme_data(results_lib, scheme_name):

    ##
    #   We only want to use test results from one scheme, so we create a filter_func that returns true
    #   for just those tests.
    ##
    filter_func = lambda test_result : test_result.get_scheme_name() == scheme_name
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
    time_data = flow_result.get_event_data("Time", include_setup=True)

    # Here, I'm just re-scaling time. It was in ms and had an offset. By subtracting the first point
    # and dividing by 1000.0, I've made it into seconds since test start.
    time_data = [(t - time_data[0]) / 1000.0 for t in time_data]

    thpt_data = flow_result.get_event_data("Throughput", include_setup=True)
    lat_data = flow_result.get_event_data("Avg Rtt", include_setup=True)
    # Throughput data is in kbps, but mbps is more understandable, so I just divide each sample by 1000.0
    thpt_data = [t / 1000.0 for t in thpt_data]

    return time_data, thpt_data, lat_data

# Below is just some standard matplotlib code. You won't be able to "show" the graph with what I did on
# line 6, but if you delete line 6, you can change the "savefig()" to "show()".
fig, axes = plt.subplots(2)
thpt_axis = axes[0]
lat_axis = axes[1]
for scheme_name in scheme_names:
    time_data, thpt_data, lat_data = get_plottable_scheme_data(results, scheme_name)
    thpt_axis.plot(time_data, thpt_data, label=scheme_name)
    lat_axis.plot(time_data, lat_data)

fig.legend()
thpt_axis.set_title(test_name)
lat_axis.set_xlabel("Time (ms)")
thpt_axis.set_ylabel("Average Throughput (mbps)")
lat_axis.set_ylabel("Average Latency (ms)")
plt.show()
