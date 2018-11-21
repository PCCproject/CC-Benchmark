#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from python_utils.file_locations import results_dir

results = ResultsLibrary(results_dir)

jitters = [0, 1, 2, 3, 4, 5, 6, 8, 10]
format_string = "jitter_30ms_%dms"

full_schemes = results.get_all_schemes_with_tests([format_string % j for j in jitters])
summary_data = {}
for scheme in full_schemes:
    summary_data[scheme] = []
    for j in jitters:
        filter_func = lambda test_result : test_result.get_scheme_name() == scheme
        scheme_results = results.get_all_results_matching(format_string % j, filter_func=filter_func)
        [scheme_result.load() for scheme_result in scheme_results]
        avg_thpt = np.mean([sr.flows["flow_1"].get_statistic("Throughput", "Mean") / 1000.0 for sr in scheme_results])
        summary_data[scheme].append(avg_thpt)

for scheme in summary_data.keys():
    print("Plotting %s, data %s" % (scheme, str(summary_data[scheme])))
    plt.plot(jitters, summary_data[scheme], label=scheme)

plt.legend()
plt.title("Average Throughput by Jitter")
plt.xlabel("Jitter (ms, from 30ms mean)")
plt.ylabel("Average Throughput (out of 30 mbps)")
plt.show()
