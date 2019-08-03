import json
import os
import numpy as np

_supported_statistics = {}

_invalid_values = {"Avg Rtt":-1.0}

def _stat_mean(trace, field, start_time=None, end_time=None):
    data = np.array(trace.get_event_data(field, start_time=start_time, end_time=end_time))
    if field in _invalid_values.keys():
        bad_indexes = np.where(data == _invalid_values[field])
        data = np.delete(data, bad_indexes)
    return np.mean(data)

def _stat_weighted_mean(trace, field, weight_field=None, start_time=None, end_time=None):
    if weight_field is None:
        return _stat_mean(trace, field)

    weights = np.array(trace.get_event_data(weight_field, start_time=start_time, end_time=end_time))
    data = np.array(trace.get_event_data(field, start_time=start_time, end_time=end_time))

    if field in _invalid_values.keys():
        bad_indexes = np.where(data == _invalid_values[field])
        weights = np.delete(weights, bad_indexes)
        data = np.delete(data, bad_indexes)

    return np.sum((weights * np.array(data))) / float(np.sum(weights))

_supported_statistics["Mean"] = _stat_mean
_supported_statistics["Ack-weighted Mean"] = lambda trace, data, start_time, end_time: _stat_weighted_mean(trace, data,
        weight_field="Acks Received", start_time=start_time, end_time=end_time)
_supported_statistics["Send-weighted Mean"] = lambda trace, data: _stat_weighted_mean(trace,
        data, weight_field="Packets Sent")

class FlowTrace():
    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        with open(filename) as f:
            self.data = json.load(f)
        self.setup_end = self.find_setup_end()
    
    def find_setup_end(self):
        setup_done = False
        cur_event = 0
        events = self.data["Events"]
        
        while (not setup_done) and cur_event < len(events):
            if (events[cur_event]["Packets Sent"] > 1):
                setup_done = True
            else:
                cur_event += 1
        
        if setup_done:
            return cur_event

        print("ERROR: Could not find end of startup for flow %s" % self.filename)
        return None

    def get_events(self, include_setup=False):
        if include_setup:
            return self.data["Events"]
        return self.data["Events"][self.setup_end:]

    def get_event_data(self, field_name, include_setup=False, start_time=None, end_time=None):
        events = self.get_events(include_setup)
        time_offset = np.float64(events[0]["Time"])
        result = []
        for event in events:
            event_time = np.float64(event["Time"]) - time_offset
            if (start_time is None or event_time >= start_time):
                #print("Event time: %s (end at %s)" % (str(event_time), str(end_time)))
                if (end_time is None or event_time <= end_time):
                    result.append(float(event[field_name]))
        return result 

    def get_statistic(self, field_name, statistic, start_time=None, end_time=None):
        if (statistic in _supported_statistics.keys()):
            return _supported_statistics[statistic](self, field_name, start_time=start_time, end_time=end_time)
        
        print("ERROR: Statistic \"%s\" is not yet implemented." % statistic)
        print("Supported statistics are %s" % str(_supported_statistics.keys()))
        return None
