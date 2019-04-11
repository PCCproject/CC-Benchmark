import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from graphing.analysis.results_library import ResultsLibrary, TestResult
from graphing.utils import data_utils
from python_utils.file_locations import results_dir
from graphing.utils import nice_names

results = ResultsLibrary(results_dir)

def _score_to_color(score):
    return (max(0.0, (100.0 - score) / 100.0), min(1.0, score / 100.0), 0)

def make_sweep_table(format_string, params, flow_name, schemes, thpt_score_func, lat_score_func, loss_score_func):
    full_schemes = results.get_all_schemes_with_tests([format_string % p for p in params])
    if schemes is not None:
        used_schemes = schemes
        full_schemes = list(set(full_schemes) & set(used_schemes))
    full_schemes = sorted(full_schemes)

    thpt_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name,
        params, format_string, "Throughput")["Mean"]
    lat_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name,
        params, format_string, "Avg Rtt")["Mean"]
    loss_data = data_utils.get_stats_dict_from_param_test(results, full_schemes, flow_name,
        params, format_string, "Loss Rate")["Mean"]

    table_cells = []
    cell_colors = []
    for scheme in full_schemes:
        thpt_score = np.mean(thpt_score_func(thpt_data[scheme]))
        lat_score = np.mean(lat_score_func(lat_data[scheme]))
        loss_score = np.mean(loss_score_func(loss_data[scheme]))
        table_cells.append(["%0.0f" % thpt_score, "%0.0f" % lat_score, "%0.0f" % loss_score])
        thpt_color = _score_to_color(thpt_score)
        lat_color = _score_to_color(lat_score)
        loss_color = _score_to_color(loss_score)
        cell_colors.append([thpt_color, lat_color, loss_color])
  
    fig, ax = plt.subplots()

    # Hide axes
    ax.axis("off")
    #ax.xaxis.set_visible(False) 
    #ax.yaxis.set_visible(False)

    ax.table(cellText=table_cells,
             cellColours=cell_colors,
             rowLabels=full_schemes,
             colLabels=["Throughput", "Latency", "Loss"])

def make_sweep_graph(format_string, params, flow_name, schemes=None,
                     show_spread=False,
                     axes=[{"data": "Throughput",
                            "name": "Link Utilization",
                            "func": "semilogx",
                            "transform": None},
                           {"data": "Avg Rtt",
                            "name": "Self-inflicted Latency (ms)",
                            "func": "semilogx",
                            "transform": None}]):

    full_schemes = results.get_all_schemes_with_tests([format_string % p for p in params])
    if schemes is not None:
        used_schemes = schemes
        full_schemes = list(set(full_schemes) & set(used_schemes))
    full_schemes = sorted(full_schemes)

    plot_data = {}
    for axis in axes:
        plot_data[axis["data"]] = data_utils.get_stats_dict_from_param_test(
                results, full_schemes, flow_name, params, format_string,
                axis["data"])

    fig, graph_axes = plt.subplots(len(axes), figsize=(5, 6))
    for scheme in full_schemes:
        for i in range(0, len(axes)):
            axis = axes[i]
            graph_axis = None
            if len(axes) == 1:
                graph_axis = graph_axes
            else:
                graph_axis = graph_axes[i]
            
            label = None
            if i == 0:
                label = nice_names.get_nice_name(scheme)

            mean_data = plot_data[axis["data"]]["Mean"][scheme]
            if axis["transform"] is not None:
                mean_data = axis["transform"](mean_data)
            if axis["func"] == "plot":
                graph_axis.plot(params, mean, label=label, linewidth=3.0)
            elif axis["func"] == "semilogx":
                graph_axis.semilogx(params, mean_data, label=label,
                                    linewidth=3.0)
            else:
                print("ERROR: Unknown plotting func %s" % axis["func"])
                exit(-1)

            if show_spread:
                min_data = plot_data[axis["data"]]["Min"][scheme]
                if axis["transform"] is not None:
                    min_data = axis["transform"](min_data)
                max_data = plot_data[axis["data"]]["Max"][scheme]
                if axis["transform"] is not None:
                    max_data = axis["transform"](max_data)
                graph_axis.fill_between(params, min_data, max_data, alpha=0.5)

                graph_axis.set_ylabel(axis["name"])

    return fig, graph_axes
