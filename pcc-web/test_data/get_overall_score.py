import os
import json
import numpy as np
import numpy.linalg as la

public_scheme = {'default_tcp', 'copa', 'vivace_latency', 'bbr'}
def get_bw_lat_from_filename(filename):
    bw = 30
    lat = 30
    detail = filename.split('-')[1]
    split = detail.split('_to_')
    # print(split)
    return (bw, lat)

def get_delay_score(metric):
    return 1 - ((metric['95 Queue Delay'] * 5) / metric['lat'])

def get_loss_score(metric):
    return 1 - ((10 * (metric['Avg Loss']/100 - metric['loss'])) / (1 - metric['loss']))

def get_overall_score_one_scheme(scheme, dir):
    # print(scheme)
    avg_thrput = []
    delay = [] #95% qing delay
    loss = []
    overall = []
    link_util = []
    delay_score = []
    loss_score = []
    for file in os.listdir(dir):
        filepath = dir + '/' + file
        if file.startswith('metric'):
            with open(filepath) as f:
                metric = json.load(f)
            # print(metric[scheme])

            avg_thrput_test = []
            delay_test = []
            loss_test = []
            overall_test = []
            link_util_stat = []
            delay_stat = []
            loss_stat = []
            bw, lat = 30, 30
            if 'jitter' not in dir:
                bw, lat = get_bw_lat_from_filename(file)
            # print(metric)
            for flow, metric in metric[scheme].items():
                avg_thrput_test.append(metric['Avg Thrput'])
                delay_test.append(metric['95 Queue Delay'])
                loss_test.append(metric['Avg Loss'] / 100)
                overall_test.append(metric['Overall'])
                link_util_stat.append(metric['Link Util'])
                delay_stat.append(get_delay_score(metric))
                loss_stat.append(get_loss_score(metric))

            avg_thrput.append(np.sum(avg_thrput_test))
            delay.append(np.sum(delay_test))
            loss.append(np.sum(loss_test))
            overall.append(np.mean(overall_test))
            link_util.append(np.sum(link_util_stat))

            delay_score_mean = np.mean(delay_stat)
            if delay_score_mean < 0:
                delay_score.append(0)
            else:
                delay_score.append(delay_score_mean)

            loss_score_mean = np.mean(loss_stat)
            if loss_score_mean < 0:
                loss_score.append(0)
            else:
                loss_score.append(loss_score_mean)

    # (Average throughput among all flows,
    #   Average 95% queueing Delay
    #   Average loss Rate
    #   Average Score,
    #   avg thrput / Capacity,
    #   delay score,
    #   loss score) f'{a:.5f}'
    return (round(np.mean(avg_thrput), 3), round(np.mean(delay), 3),
    round(np.mean(loss), 3), round(np.mean(overall), 3),
    round(np.mean(link_util) / 100, 3), round(np.mean(delay_score_mean), 3),
    round(np.mean(loss_score), 3))

def add_metric_to_res(scheme, metric, testres):
    testres['avg thrput'][scheme] = metric[0]
    testres['95 qdelay'][scheme] = metric[1]
    testres['avg loss'][scheme] = metric[2]
    testres['overall'][scheme] = metric[3]
    testres['avg thrput'][scheme + ' score'] = metric[4]
    testres['95 qdelay'][scheme + ' score'] = metric[5]
    testres['avg loss'][scheme + ' score'] = metric[6]
    testres['overall'][scheme + ' score'] = metric[6]

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

    with open("public_scheme_metrics.json", 'w') as f:
        f.write(json.dumps(public_res, indent=4))

    with open("indev_scheme_metrics.json", 'w') as f:
        f.write(json.dumps(indev_res, indent=4))
