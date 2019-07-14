import json
import os
import sys
import numpy as np
import math

def get95QueueDelay(data, base_latency):
    events = data["Events"]
    queueing_delay = []
    for event in events:
        avg_rtt = float(event['Avg Rtt'])
        queueing_delay.append(avg_rtt - base_latency)

    return np.percentile(queueing_delay, 95)

def getAvgThrput(data):
    events = data["Events"]
    thrput = np.array([float(event['Throughput']) for event in events])
    return np.mean(thrput)

def getLinkUtilization(data, link_capacity): #link capacity in mbps
    avgThrput = getAvgThrput(data)
    return avgThrput / (link_capacity * 1e3) * 100

def get95Lat(data):
    events = data["Events"]
    lat = np.array([float(event['Avg Rtt']) for event in events])
    return np.percentile(lat, 95)

def getAvgLat(data):
    events = data["Events"]
    lat = []
    for event in events:
        rtt = float(event["Avg Rtt"])
        if rtt < 0:
            lat.append(0)
        else:
            lat.append(rtt)
    return np.mean(lat)

def getAvgLoss(data):
    events = data["Events"]
    loss = np.array([float(event['Loss Rate']) for event in events])
    return np.mean(loss)

def getKleinrock(data):
    return np.log(getAvgThrput(data) / get95Lat(data))

def getMetricScore(data, bw, lat, loss=0):
    # Units [kbps, ms, %, None, %, ms]
    return {
        "Avg Thrput":getAvgThrput(data) / 1000,
        "Avg Lat":getAvgLat(data),
        "Avg Loss":getAvgLoss(data),
        "Overall":getKleinrock(data),
        "Link Util":getLinkUtilization(data, bw),
        "95 Queue Delay":get95QueueDelay(data, lat),
        "bw": bw,
        "lat": lat,
        "loss": loss
    }

def getTimeThrputFromJson(data):
    points = []
    start_time = float(data['Events'][0]['Time'])
    thrput = 0
    for e in data['Events']:
        curr_data = {'Time':float(e['Time']) - start_time, 'Throughput':e['Throughput'], 'Avg Rtt': e['Avg Rtt']}
        thrput += float(e['Throughput'])
        points.append(curr_data)

    return points, thrput / len(data['Events'])

def getJainIndex(mean_thrput):
    sum_sq = sum(mean_thrput) ** 2
    sqrd_sum = sum([math.pow(x, 2) for x in mean_thrput])

    return sum_sq / (len(mean_thrput) * sqrd_sum)
