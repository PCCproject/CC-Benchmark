#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

results = ResultsLibrary(results_dir)

param_name = "Bandwidth"
param_unit = "mbps"
params = [1, 2, 4, 8, 16, 32, 64, 128]
format_string = "simple_%dmbps"

full_schemes = sorted(results.get_all_schemes_with_tests([format_string % p for p in params]))
thpt_data = {}
fig, axes = plt.subplots(2)
thpt_axis = axes[0]
lat_axis = axes[1]
for scheme in full_schemes:
    filter_func = lambda test_result : test_result.get_scheme_name() == scheme
    thpt_data = []
    lat_data = []
    for p in params:
        scheme_results = results.get_all_results_matching(format_string % p, filter_func=filter_func)
        [scheme_result.load() for scheme_result in scheme_results]
        avg_thpt = np.mean([sr.flows["flow_1"].get_statistic("Throughput", "Mean") / float(p * 1000.0) for sr in scheme_results])
        avg_lat = np.mean([sr.flows["flow_1"].get_statistic("Avg Rtt", "Mean") for sr in scheme_results])
        thpt_data.append(avg_thpt)
        lat_data.append(avg_lat)
    thpt_axis.plot(params, thpt_data, label=scheme)
    lat_axis.plot(params, lat_data)

fig.legend()
thpt_axis.set_title("%s Test Performance" % param_name)
lat_axis.set_xlabel("%s (%s)" % (param_name, param_unit))
thpt_axis.set_ylabel("Average Throughput (mbps)")
lat_axis.set_ylabel("Average Latency (ms)")
plt.show()
