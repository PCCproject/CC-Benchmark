import os
import json
import numpy as np
import numpy.linalg as la

class test_params:
    def __init__(self, bw, lat, loss):
        self.bw = bw
        self.lat = lat
        self.loss = loss

    def __key(self):
        return (self.bw, self.lat, self.loss)

    def __eq__(self, other):
        return (isinstance(other, type(self)) and self.__key() == other.__key())

    def __hash__(self):
        return hash(self.__key()) ^ hash(self.bw) ^ hash(self.lat) ^ hash(self.loss)

    def __repr__(self):
        return "{}, {}, {}".format(self.bw, self.lat, self.loss)

public_scheme = {'default_tcp', 'copa', 'vivace_latency', 'bbr'}

def get_average_test_params(metrics):
    bw = []
    lat = []
    loss = []

    for flow, metric in metrics.items():
        bw.append(metric['bw'])
        lat.append(metric['lat'])
        loss.append(metric['loss'])

    return test_params(round(np.mean(bw), 5), round(np.mean(lat), 5), round(np.mean(loss), 5))

def average_metrics(metrics):
    for k, v in metrics.items():
        metrics[k] = np.mean(v)

def get_avg_thrput_and_linkutil(link_util_stat):
    avg_thrput = np.mean([value for value in link_util_stat.values()])
    avg_linkcap = np.mean([metric.bw for metric in link_util_stat.keys()])

    return avg_thrput, avg_thrput / avg_linkcap

def get_mean_metric_and_score(metric_stat):
    return np.mean([value for value in metric_stat.values()])

def get_avg_loss_and_lossscore(loss_stat):
    avg_loss = np.mean([value for value in loss_stat.values()])
    avg_rand_loss = np.mean([metric.loss for metric in loss_stat.keys()])
    num = avg_loss - avg_rand_loss
    denom = 1 - avg_rand_loss

    return avg_loss, (1 - 10*(num/denom))

def get_avg_delay_and_delayscore(delay_stat):
    avg_delay = np.mean([value for value in delay_stat.values()])
    # base_delay = np.mean([metric.lat for metric in delay_stat.keys()])
    # score = 1 - ((3 * avg_delay) / base_delay)
    score = 1 - (avg_delay / 30)
    # return avg_delay, score
    return avg_delay, score

def get_overall_score_one_scheme(scheme, dir):
    # print(scheme)
    avg_thrput = []
    delay = [] #95% qing delay
    loss = []
    overall = []
    link_util = []
    delay_score = []
    loss_score = []

    link_util_stat = {}
    delay_stat = {}
    loss_stat = {}
    overall_stat = {}

    for file in os.listdir(dir):
        filepath = dir + '/' + file
        if file.startswith('metric'):
            with open(filepath) as f:
                metrics = json.load(f)

            test_param = get_average_test_params(metrics[scheme])
            # print(test_param)
            avg_thrput_test = []
            delay_test = []
            loss_test = []
            overall_test = []

            # print(metric)
            for flow, metric in metrics[scheme].items():
                avg_thrput_test.append(metric['Avg Thrput'])
                delay_test.append(metric['95 Queue Delay'])
                loss_test.append(metric['Avg Loss'])
                overall_test.append(metric['Overall'])

            if test_param not in link_util_stat:
                link_util_stat[test_param] = []
                delay_stat[test_param] = []
                loss_stat[test_param] = []
                overall_stat[test_param] = []

            link_util_stat[test_param].append(np.sum(avg_thrput_test))
            delay_stat[test_param].append(np.mean(delay_test))
            loss_stat[test_param].append(np.mean(loss_test))
            overall_stat[test_param].append(np.mean(overall_test))

    average_metrics(link_util_stat)
    average_metrics(delay_stat)
    average_metrics(loss_stat)
    average_metrics(overall_stat)

    avg_thrput, thrput_score = get_avg_thrput_and_linkutil(link_util_stat)
    avg95_delay, delay_score = get_avg_delay_and_delayscore(delay_stat)
    avg_loss, loss_score = get_avg_loss_and_lossscore(loss_stat)
    overall_score = get_mean_metric_and_score(overall_stat)

    # print(avg_thrput, thrput_score, avg95_delay, delay_score, avg_loss, loss_score, overall_score)
    # (Average throughput among all flows,
    #   Average 95% queueing Delay
    #   Average loss Rate
    #   Average Score,
    #   avg thrput / Capacity,
    #   delay score,
    #   loss score)
    return (round(avg_thrput, 3), round(avg95_delay, 3), round(avg_loss, 3), round(overall_score, 3),
    round(thrput_score, 3), round(delay_score, 3), round(loss_score, 3))

def add_metric_to_res(scheme, metric, testres):
    testres['avg thrput'][scheme] = metric[0]
    testres['95 qdelay'][scheme] = metric[1]
    testres['avg loss'][scheme] = metric[2]
    testres['overall'][scheme] = metric[3]
    testres['overall'][scheme + ' score'] = (metric[3] / 5)
    testres['avg thrput'][scheme + ' score'] = metric[4]
    testres['95 qdelay'][scheme + ' score'] = metric[5]
    testres['avg loss'][scheme + ' score'] = metric[6]

def get_overall_score(dir):
    public_res = {"Tests": []}
    indev_res = {"Tests": []}
    for testname in os.listdir(dir):
        testpath = dir + testname
        public_testres = {"name":testname, "avg thrput":{},
                                            "95 qdelay": {},
                                            "avg loss": {},
                                            "overall": {}}
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

    with open(dir + "/public_scheme_metrics.json", 'w') as f:
        f.write(json.dumps(public_res, indent=4))

    with open(dir + "/indev_scheme_metrics.json", 'w') as f:
        f.write(json.dumps(indev_res, indent=4))
