import json
import numpy as np

def convert_interval_to_event(lines, start_line_number, start_time, end_time):
    bytes_sent = 0
    bytes_acked = 0
    packets_sent = 0
    acks_received = 0
    rtt_samples = []
    global _printed_info

    cur_time = start_time
    cur_line_number = start_line_number
    first_packet_sent_time = start_time
    last_packet_sent_time = 0
    while cur_time < end_time and cur_line_number < len(lines):
        line = lines[cur_line_number]
        cur_time = float(line[0])
        sent_time = cur_time
        if "+" in line:
            bytes_sent += int(line[2])
            packets_sent += 1
        else:
            bytes_acked += int(line[2])
            acks_received += 1
            rtt_samples.append(float(line[3]))
            sent_time = round(cur_time - float(line[3]), 3)
            if (sent_time < first_packet_sent_time):
                first_packet_sent_time = sent_time
            if (sent_time > last_packet_sent_time):
                last_packet_sent_time = sent_time
        cur_line_number += 1

    bytes_should_have_been_acked = 0
    packets_should_have_been_acked = 0
    if (len(rtt_samples) > 0):
        backtrack_line_number = cur_line_number - 1
        while (cur_time >= first_packet_sent_time and backtrack_line_number >= 0):
            line = lines[backtrack_line_number]
            cur_time = round(float(line[0]), 3)

            if cur_time >= first_packet_sent_time and cur_time <= last_packet_sent_time and "+" in line:
                bytes_should_have_been_acked += int(line[2])
                packets_should_have_been_acked += 1
            backtrack_line_number -= 1

    dur = (end_time - start_time)
    throughput = 1000 * 8.0 * bytes_acked / dur
    send_rate = 1000 * 8.0 * bytes_sent / dur

    avg_rtt = min_rtt = max_rtt = -1.0
    if len(rtt_samples) > 0:
        avg_rtt = np.mean(rtt_samples)
        min_rtt = np.min(rtt_samples)
        max_rtt = np.max(rtt_samples)
    loss_rate = 0.0
    if bytes_should_have_been_acked > 0:
        loss_rate = (bytes_should_have_been_acked - bytes_acked) / float(bytes_should_have_been_acked)
    if bytes_should_have_been_acked < bytes_acked:
        print("Warning: Conversion of Pantheon log failed align ACKs and expected ACKs")
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
        "Acks Received":acks_received,
        "Packets Should Have Been Acked":packets_should_have_been_acked
    }
    return event, cur_line_number

def get_base_rtt(lines):
    start_time = float(lines[0][0])
    end_time = float(lines[-1][0])
    event, lines_used = convert_interval_to_event(lines, 0, start_time, end_time)
    return float(event["Five Percent Rtt"])

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
    base_rtt = get_base_rtt(lines)

    events = []
    cur_line_number = 0
    cur_start_time = 0.0
    dur = base_rtt
    print("Converting log with base RTT: %f" % base_rtt)
    start_time = float(lines[0][0])
    end_time = float(lines[-1][0])
    print("Log has %d lines" % len(lines))
    print("Log spans time %d to %d" % (start_time, end_time))
    print("Expecting to convert log into %d intervals" % ((end_time - start_time) / base_rtt))
    while cur_line_number < len(lines):
        new_event, lines_used = convert_interval_to_event(lines, cur_line_number,
            cur_start_time, cur_start_time + dur)
        new_event["Time"] = str(float(new_event["Time"]) + start_timestamp)
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
