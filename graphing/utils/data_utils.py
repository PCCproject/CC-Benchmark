import numpy as np

def get_scheme_stats_from_param_test(results_lib, scheme, flow, params, format_str, value,
        statistic="Mean", flow_combo_func=np.mean, start_time=None, end_time=None):
    
    filter_func = lambda test_result : test_result.get_scheme_name() == scheme
    data = []
    for p in params:
        scheme_results = results_lib.get_all_results_matching(format_str % p,
                filter_func=filter_func)
        [scheme_result.load() for scheme_result in scheme_results]
        flows = [sr.flows[flow] for sr in scheme_results]
        data.append(flow_combo_func([flow.get_statistic(value, statistic, start_time, end_time) for flow in flows]))

    return data

def get_stats_dict_from_param_test(results_lib, schemes, flow, params,
        format_str, value, statistic="Mean"):

    data = {"Mean":{}, "Min":{}, "Max":{}}
    for scheme in schemes:
        data["Mean"][scheme] = get_scheme_stats_from_param_test(results_lib,
                scheme, flow, params, format_str, value, statistic, np.mean)
        data["Min"][scheme] = get_scheme_stats_from_param_test(results_lib,
                scheme, flow, params, format_str, value, statistic, np.min)
        data["Max"][scheme] = get_scheme_stats_from_param_test(results_lib,
                scheme, flow, params, format_str, value, statistic, np.max)

    return data

def get_startup_stats_dict_from_param_test(results_lib, schemes, flow, params,
        format_str, value, statistic="Mean", cutoff_msec=10000.0):

    data = {"Mean":{}, "Min":{}, "Max":{}}
    for scheme in schemes:
        data["Mean"][scheme] = get_scheme_stats_from_param_test(results_lib,
                scheme, flow, params, format_str, value, statistic, np.mean,
                end_time=cutoff_msec)
        data["Min"][scheme] = get_scheme_stats_from_param_test(results_lib,
                scheme, flow, params, format_str, value, statistic, np.min,
                end_time=cutoff_msec)
        data["Max"][scheme] = get_scheme_stats_from_param_test(results_lib,
                scheme, flow, params, format_str, value, statistic, np.max,
                end_time=cutoff_msec)

    return data
