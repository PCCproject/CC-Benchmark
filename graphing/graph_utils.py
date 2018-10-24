import json
import numpy as np
import multiprocessing

def convert_interval_to_event(lines, start_line_number, start_time, end_time):
    bytes_sent = 0
    bytes_acked = 0
    packets_sent = 0
    acks_received = 0
    rtt_samples = []

    cur_time = start_time
    cur_line_number = start_line_number
    #print("start_time %f, end_time %f" % (start_time, end_time))
    while cur_time < end_time and cur_line_number < len(lines):
        line = lines[cur_line_number]
        cur_time = float(line[0])
        sent_time = cur_time
        if "-" in line:
            sent_time = cur_time - float(line[3])
        #if sent_time >= start_time and sent_time <= end_time:
        if "+" in line:
            bytes_sent += int(line[2])
            packets_sent += 1
        else:
            bytes_acked += int(line[2])
            acks_received += 1
            rtt_samples.append(float(line[3]))
        cur_line_number += 1

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
        loss_rate = (bytes_sent - bytes_acked) / float(bytes_sent)
    if loss_rate < 0:
        loss_rate = 0
    latency_inflation = 0
    if len(rtt_samples) >= 2:
        latency_inflation = (rtt_samples[-1] - rtt_samples[0]) / dur
    
    event = {
        "Name":"Sample",
        "Time":str(start_time),
        "Throughput":str(throughput / 1e3),
        "Target Rate":str(send_rate / 1e3),
        "Avg Rtt":str(avg_rtt),
        "Min Rtt":str(min_rtt),
        "Max Rtt":str(max_rtt),
        "Loss Rate":str(loss_rate),
        "Rtt Inflation":str(latency_inflation),
        "Packets Sent":packets_sent,
        "Acks Received":acks_received
    }
    return event, cur_line_number

def get_base_rtt(lines):
    start_time = float(lines[0][0])
    event, lines_used = convert_interval_to_event(lines, 0, start_time, 10000.0)
    print(event)
    return float(event["Min Rtt"])

def convert_file_to_data_dict(filename):
    print("Reading data from %s" % filename)
    lines = []
    with open(filename) as f:
        lines = f.readlines()

    good_lines = []
    for line in lines:
        if "#" not in line: # Remove comments
            good_lines.append(line.split(" "))

    lines = good_lines
    base_rtt = get_base_rtt(lines)
    print("Converting log into slices of %f ms" % base_rtt)

    events = []
    cur_line_number = 0
    cur_start_time = 0.0
    dur = base_rtt
    while cur_line_number < len(lines):
        new_event, lines_used = convert_interval_to_event(lines, cur_line_number,#[cur_line_number:],
            cur_start_time, cur_start_time + dur)
        cur_line_number = lines_used
        cur_start_time += dur
        events.append(new_event)

    return {"Events":events}

def convert_pantheon_log(pantheon_filename, converted_filename, delete_old=False):
    data_dict = convert_file_to_data_dict(pantheon_filename)
    with open(converted_filename, "w") as outf:
        json.dump(data_dict, outf, indent=4)
    if delete_old:
        os.remove(pantheon_filename)
