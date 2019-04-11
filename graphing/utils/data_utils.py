import numpy as np

def get_scheme_stats_from_param_test(results_lib, scheme, flow, params, format_str, value,
        statistic="Mean", flow_combo_func=np.mean):
    
    filter_func = lambda test_result : test_result.get_scheme_name() == scheme
    data = []
    for p in params:
        scheme_results = results_lib.get_all_results_matching(format_str % p,
                filter_func=filter_func)
        [scheme_result.load() for scheme_result in scheme_results]
        flows = [sr.flows[flow] for sr in scheme_results]
        data.append(flow_combo_func([flow.get_statistic(value, statistic) for flow in flows]))

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
