import os
import json
import numpy as np
import numpy.linalg as la

test_data_dir = '/Users/jaewooklee/PCC-Tester/pcc-web/test_data/'
public_scheme = {'default_tcp', 'copa', 'vivace_latency', 'bbr'}
def get_overall_score_one_scheme(scheme, dir):
    # print(scheme)
    link_util = []
    delay = [] #95% qing delay
    loss = []
    overall = []
    for file in os.listdir(dir):
        filepath = dir + '/' + file
        if file.startswith('metric'):
            with open(filepath) as f:
                metric = json.load(f)

            # print(metric[scheme])
            for flow, metric in metric[scheme].items():
                link_util.append(metric['Avg Thrput'])
                delay.append(metric['95 Queue Delay'])
                loss.append(metric['Avg Loss'])
                overall.append(metric['Overall'])

    # (Sum of link utilization of all flows,
    #   Average 95% queueing Delay
    #   Average loss Rate
    #   Average Score)
    return (np.sum(link_util), np.mean(delay), np.mean(loss), np.mean(overall))

def add_metric_to_res(scheme, metric, testres):
    testres['avg thrput'][scheme] = metric[0]
    testres['95 qdelay'][scheme] = metric[1]
    testres['avg loss'][scheme] = metric[2]
    testres['overall'][scheme] = metric[3]

def normalize(data):
    testres = data["Tests"]
    for testdata in testres:
        for k, v in testdata.items():
            if k != 'name':
                denom = la.norm([x for x in v.values()], 1)
                for scheme, stat in v.items():
                    if denom == 0:
                        v[scheme] = 1
                    else:
                        v[scheme] /= denom

def get_overall_score(dir):
    public_res = {"Tests": []}
    indev_res = {"Tests": []}
    for testname in os.listdir(dir):
        testpath = dir + testname
        public_testres = {"name":testname, "avg thrput":{}, "95 qdelay": {}, "avg loss": {}, "overall": {}}
        indev_testres = {"name":testname, "avg thrput":{}, "95 qdelay": {}, "avg loss": {}, "overall": {}}
        if 'py' not in testname and os.path.isdir(testpath):
            datadir = testpath + '/data/'
            for scheme in os.listdir(datadir):
                scheme_path = datadir + scheme
                if os.path.isdir(scheme_path) and not scheme_path.startswith('.'):
                    metric = get_overall_score_one_scheme(scheme, scheme_path)

                    if scheme in public_scheme:
                        add_metric_to_res(scheme, metric, public_testres)
                    else:
                        add_metric_to_res(scheme, metric, indev_testres)
            if len(public_testres['avg thrput']) > 0:
                public_res["Tests"].append(public_testres)
            if len(indev_testres['avg thrput']) > 0:
                indev_res["Tests"].append(indev_testres)

    normalize(public_res)
    normalize(indev_res)

    with open("public_scheme_metrics.json", 'w') as f:
        f.write(json.dumps(public_res, indent=4))

    with open("indev_scheme_metrics.json", 'w') as f:
        f.write(json.dumps(indev_res, indent=4))


get_overall_score('/Users/jaewooklee/PCC-Tester/pcc-web/test_data/')
