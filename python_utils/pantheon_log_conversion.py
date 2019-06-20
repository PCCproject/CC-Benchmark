import math
import json
import numpy as np

def convert_interval_to_event(packet_events, start_event_number, start_time, end_time):
    bytes_sent = 0
    bytes_acked = 0
    packets_sent = 0
    rtt_samples = []
    global _printed_info

    cur_time = start_time
    cur_event_number = start_event_number
    first_packet_sent_time = start_time
    last_packet_sent_time = 0
    while cur_time < end_time and cur_event_number < len(packet_events):
        event = packet_events[cur_event_number]
        cur_time = event.time
        if event.type == INGRESS:
            bytes_sent += event.bytes
            packets_sent += 1
            if (event.was_acked == True) or (event.was_acked is None):
                bytes_acked += event.bytes
        elif event.type == EGRESS:
            rtt_samples.append(event.rtt)
        else:
            print("ERROR: Unknown event type!")
        cur_event_number += 1

    dur = (end_time - start_time)
    throughput = 1000 * 8.0 * bytes_acked / dur
    send_rate = 1000 * 8.0 * bytes_sent / dur

    avg_rtt = min_rtt = max_rtt = -1.0
    if len(rtt_samples) > 0:
        avg_rtt = np.mean(rtt_samples)
        min_rtt = np.min(rtt_samples)
        max_rtt = np.max(rtt_samples)
    loss_rate = 0.0
    if bytes_sent > 0:
        loss_rate = 1.0 - (bytes_acked / bytes_sent)
    latency_inflation = 0
    five_percent_rtt = -1.0
    if len(rtt_samples) >= 2:
        latency_inflation = (rtt_samples[-1] - rtt_samples[0]) / dur
        five_percent_rtt = np.percentile(np.array(rtt_samples), 5)

    event = {
        "Name":"Sample",
        "Time":str(start_time),
        "Throughput":str(throughput / 1e3),
        "Target Rate":str(send_rate / 1e3),
        "Five Percent Rtt":str(five_percent_rtt),
        "Avg Rtt":str(avg_rtt),
        "Min Rtt":str(min_rtt),
        "Max Rtt":str(max_rtt),
        "Loss Rate":str(loss_rate),
        "Rtt Inflation":str(latency_inflation),
        "Packets Sent":packets_sent,
        "Acks Received":len(rtt_samples)
    }
    return event, cur_event_number

def get_base_rtt(packet_events):
    start_time = packet_events[0].time
    end_time = packet_events[-1].time
    event, events_used = convert_interval_to_event(packet_events, 0, start_time, end_time)
    return float(event["Five Percent Rtt"])

INGRESS = 'I'
EGRESS = 'E'

class PacketEvent():

    def __init__(self, line):
        if len(line) < 3:
            print("Warning: Could not convert line of Pantheon log:")
            print("\t%s" % str(line))
            self.time = None
            return
        self.time = round(float(line[0]), 3)
        self.bytes = int(line[2])
        self.type = INGRESS
        self.was_acked = None
        if "-" in line:
            self.type = EGRESS
            self.rtt = round(float(line[3]), 3)

    def matches_egress(self, egress_event):
        return abs(self.time - (egress_event.time - egress_event.rtt)) < 0.0001

    def was_sent_too_early_for_egress(self, egress_event):
        return (self.time < egress_event.time - egress_event.rtt)

def create_packet_events(lines):
    packet_events = []
    for line in lines:
        try:
            event = PacketEvent(line)
            if event.time is not None:
                packet_events.append(event)
        except Exception as e:
            print("Warning: Could not convert Pantheon log line %s" % str(line))
    return packet_events

def advance_ingress_ptr(ingress_ptr, packet_events):
    ingress_ptr += 1
    while (ingress_ptr < len(packet_events)) and (packet_events[ingress_ptr].type == EGRESS):
        ingress_ptr += 1
    return ingress_ptr

def mark_acked_packets(packet_events):
    end_ptr = len(packet_events)
    ingress_ptr = advance_ingress_ptr(-1, packet_events)
    egress_events = []
    for e in packet_events:
        if e.type == EGRESS:
            egress_events.append(e)
    sorted_egress_events = sorted(egress_events, key=lambda x: x.time - x.rtt)
    egress_ptr = 0

    while (ingress_ptr < end_ptr) and (egress_ptr < len(sorted_egress_events)):
        if packet_events[ingress_ptr].matches_egress(sorted_egress_events[egress_ptr]):
            #print("\tMatch!")
            packet_events[ingress_ptr].was_acked = True
            ingress_ptr = advance_ingress_ptr(ingress_ptr, packet_events)
            egress_ptr += 1
        elif packet_events[ingress_ptr].was_sent_too_early_for_egress(sorted_egress_events[egress_ptr]):
            #print("\tMiss. Ingress was not acked.")
            packet_events[ingress_ptr].was_acked = False
            ingress_ptr = advance_ingress_ptr(ingress_ptr, packet_events)
        else:
            print("Warning: Could not match egress event to packet ingress:")
            print("\tEgress time: %f" % sorted_egress_events[egress_ptr].time)
            print("\tEgress Rtt: %f" % sorted_egress_events[egress_ptr].rtt)
            print("\tEstimated Ingress: %f" % (sorted_egress_events[egress_ptr].time - sorted_egress_events[egress_ptr].rtt))
            print("\tBest candidate ingress time: %f" % packet_events[ingress_ptr].time)
            print("\tDifference: %f" % (packet_events[ingress_ptr].time - (sorted_egress_events[egress_ptr].time - sorted_egress_events[egress_ptr].rtt)))
            egress_ptr += 1
            #exit(-1)
    return

def convert_file_to_data_dict(filename):
    lines = []
    with open(filename) as f:
        lines = f.readlines()

    start_timestamp = float(lines[0].split(" ")[-1])
    good_lines = []
    for line in lines:
        if "#" not in line: # Remove comments
            good_lines.append(line.split(" "))

    lines = good_lines
    packet_events = create_packet_events(lines)
    mark_acked_packets(packet_events)
    total_packets = sum([1 if e.type == INGRESS else 0 for e in packet_events])
    lost_packets = sum([1 if e.type == INGRESS and (e.was_acked == False) else 0 for e in packet_events])
    unknown_packets = sum([1 if e.type == INGRESS and (e.was_acked is None) else 0 for e in packet_events])
    print("Lost %d/%d packets" % (lost_packets, total_packets))
    print("Unknown %d/%d packets" % (unknown_packets, total_packets))
    base_rtt = get_base_rtt(packet_events)

    events = []
    cur_event_number = 0
    cur_start_time = 0.0
    dur = base_rtt
    print("Converting log with base RTT: %f" % base_rtt)
    start_time = packet_events[0].time
    end_time = packet_events[-1].time
    print("Log has %d events" % len(packet_events))
    print("Log spans time %d to %d" % (start_time, end_time))
    print("Expecting to convert log into %d intervals" % ((end_time - start_time) / base_rtt))
    #exit(-1)
    while cur_event_number < len(packet_events):
        new_event, events_used = convert_interval_to_event(packet_events, cur_event_number,
            cur_start_time, cur_start_time + dur)
        new_event["Time"] = str(float(new_event["Time"]) + start_timestamp)
        cur_event_number = events_used
        cur_start_time += dur
        events.append(new_event)

    return {"Events":events}

def validate_attr(data_list, attr):
    if attr is None:
        raise ValueError("Attr cannot be None")
        return
    if attr not in data_list[0]:
        raise KeyError()
        return

def get_mean_of_attr(data_list, attr=None):
    validate_attr(data_list, attr)
    return sum([float(x[attr]) for x in data_list])

def get_sum_of_attr(data_list, attr=None):
    validate_attr(data_list, attr)
    return np.mean(np.array([float(x[attr]) for x in data_list]))

def get_ith_time(event, i):
    return float(event[i]["Time"])

def get_batch_size(data_dict, nearest=1):
    nearest_ms = nearest * 1000
    time_til_now = 0

    batch_size = 1
    events = data_dict['Events']
    i = 0
    while time_til_now < nearest_ms:
        time_til_now += (get_ith_time(events, i + 1) - get_ith_time(events, i))
        i += 1

    return i

def merge_n_logs(data_list):
    """
    Given n events it merges the events into 1 event
    'Five Percent Rtt', 'Name', 'Avg Rtt', 'Max Rtt', 'Min Rtt' are neglected
    """
    data_dict = {"Loss Rate": get_mean_of_attr(data_list, "Loss Rate"),
                 "Avg Rtt": get_mean_of_attr(data_list, "Avg Rtt"),
                 "Acks Received": get_sum_of_attr(data_list, "Acks Received"),
                 "Target Rate": get_mean_of_attr(data_list, "Target Rate"),
                 "Rtt Inflation": get_mean_of_attr(data_list, "Rtt Inflation"),
                 "Throughput" : get_mean_of_attr(data_list, "Throughput"),
                 "Packets Sent": get_sum_of_attr(data_list, "Packets Sent"),
                 "Time": data_list[0]["Time"],
                 }

    return data_dict

def merge_logs_by_batch_size(data_dict, batch_size):
    all_data = []
    i = 0
    data_list = data_dict['Events']
    while i < len(data_list):
        all_data.append(merge_n_logs(data_list[i : i + batch_size]))
        i += batch_size
    if len(data_list[i:]) > 0:
        all_data.append(merge_n_logs(data_list[i:]))

    return {"Events" : all_data}

def convert_pantheon_log(pantheon_filename, converted_filename, delete_old=False):
    data_dict = convert_file_to_data_dict(pantheon_filename)
    batch_size = get_batch_size(data_dict)
    new_data = merge_logs_by_batch_size(data_dict, batch_size)

    with open(converted_filename.split(".json")[0]+"_orig.json", "w") as outf:
        json.dump(data_dict, outf, indent=4)

    with open(converted_filename, "w") as outf:
        json.dump(new_data, outf, indent=4)
    if delete_old:
        os.remove(pantheon_filename)
