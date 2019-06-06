#!/usr/bin/python3
import os
import sys


for l in os.listdir("./tests/rtt_fairness4"):
    if l.startswith("all"):
        continue
    latencies = l.split("ms_to_")
    first_lat = latencies[0]
    second_lat = latencies[1]
    thrid_lat = latencies[2].split("ms")[0]

    cmd = "./rtt_fairness4_graph.py {} {} {}".format(first_lat, second_lat, thrid_lat)
    os.system(cmd)
