import json
import os
import sys
import numpy as np

def extract_xcoord_from_name(name):
    ret = ''
    for c in name:
        if c.isdigit():
            ret += c
        else:
            break
    return int(ret)

def _add_jain_idx(scheme_list, to_add):
    for elem in scheme_list:
        if int(elem['x']) == int(to_add['x']):
            elem['y'].append(to_add['y'])
            return
    scheme_list.append({'x':to_add['x'], 'y':[to_add['y']]})

def _merge_jain_idx(scheme_dir):
    scheme = scheme_dir.split('/')[-1]
    res = []
    for file in os.listdir(scheme_dir):
        if not file.startswith('.DS') and not file.startswith('metric'):
            file_path = scheme_dir + '/' + file
            with open(file_path) as f:
                obj = json.load(f)
                try:
                    x = obj['Ratio']
                except:
                    x = extract_xcoord_from_name(file) 
                y = obj['Jain idx']
                to_add = {'x':x, 'y':y}
                _add_jain_idx(res, to_add)

    for elem in res:
        elem['y'] = np.mean(elem['y'])

    return res

def merge_jain_idx_in_dir(data_dir):
    merged = {}
    for scheme in os.listdir(data_dir):
        if not scheme.startswith('.DS'):
            merged[scheme] = _merge_jain_idx(data_dir + scheme)

    with open(data_dir + '../jain.json', 'w') as f:
        f.write(json.dumps(merged, indent=4))

def merge_all_jain_idx_with_multiflow(test_data_dir, multiflow_dir):
    for mult_dir in multiflow_dir:
        merge_jain_idx_in_dir(test_data_dir + mult_dir + '/data/')
