import json
import os
import sys
import numpy as np
from pprint import pprint

def _average_single_merged_metric(merged_metric):
    sum = set(['Avg Thrput', 'Link Util'])
    # sum.add('Avg Thrput')
    # add more if necessary

    for k in merged_metric.keys():
        # print(k)
        if k in sum:
            merged_metric[k] = np.sum(merged_metric[k])
        else:
            merged_metric[k] = np.mean(merged_metric[k])
    return merged_metric

def _merge_single_trial(metric):
    merged_metric = {}
    for flow, detail in metric.items():
        for field, value in metric[flow].items():
            # print(field)
            if not field in merged_metric:
                merged_metric[field] = []
            merged_metric[field].append(value)

    return _average_single_merged_metric(merged_metric)

def _merge_multiple_test(metrics_list):
    if len(metrics_list) == 1:
        return metrics_list[0]

    merged_metric = {}
    for metric in metrics_list:
        for k, v in metric.items():
            if k not in merged_metric:
                merged_metric[k] = []
            merged_metric[k].append(v)
    # print(merged_metric)

    for k, v in merged_metric.items():
        merged_metric[k] = np.mean(merged_metric[k])

    return merged_metric

def average_all_trials(metrics):
    # pprint(metrics)
    for scheme in metrics.keys():
        # print(scheme)
        for detail, metric in metrics[scheme].items():
            metrics[scheme][detail] = _merge_multiple_test(metrics[scheme][detail])

    return metrics

def merge_metric_for_all_test(test_data_dir, multiflow_dir):
    for test_dir in os.listdir(test_data_dir):
        test_path = test_data_dir + test_dir
        if os.path.isdir(test_path) and 'pycache' not in test_dir:
            data_path = test_path + '/data/'
            res = {}
            os.system('mkdir -p {}'.format(data_path))
            for scheme in os.listdir(data_path):
                scheme_path = data_path + scheme
                if os.path.isdir(scheme_path):
                    res[scheme] = {}
                    for file in os.listdir(scheme_path):
                        filepath = scheme_path + '/' + file
                        if file.startswith('metric'):
                            # print(scheme)
                            # print(filepath)
                            with open(filepath) as f:
                                metric = json.load(f)
                            if len(metric[scheme]) > 1:
                                multiflow_dir.add(test_dir)
                                metric = _merge_single_trial(metric[scheme])
                            else:
                                metric = metric[scheme]['flow1']

                            test_detail = str(file.split('-')[1])
                            if test_detail not in res[scheme]:
                                res[scheme][test_detail] = []
                            res[scheme][test_detail].append(metric)
            if len(res) > 0:
                # pprint(res)
                res = average_all_trials(res)
                metric_file_name = test_path + '/metrics.json'
                with open(metric_file_name, 'w') as f:
                    f.write(json.dumps(res, indent=4))
