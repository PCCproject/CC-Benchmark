import json
import os
import numpy as np

_supported_statistics = {}

_invalid_values = {"Avg Rtt":-1.0}

def _stat_mean(trace, field):
    data = np.array(trace.get_event_data(field))
    if field in _invalid_values.keys():
        bad_indexes = np.where(data == _invalid_values[field])
        data = np.delete(data, bad_indexes)
    return np.mean(data)

def _stat_weighted_mean(trace, field, weight_field=None):
    if weight_field is None:
        return _stat_mean(trace, field)

    weights = np.array(trace.get_event_data(weight_field))
    data = np.array(trace.get_event_data(field))

    if field in _invalid_values.keys():
        bad_indexes = np.where(data == _invalid_values[field])
        weights = np.delete(weights, bad_indexes)
        data = np.delete(data, bad_indexes)

    return np.sum((weights * np.array(data))) / float(np.sum(weights))

_supported_statistics["Mean"] = _stat_mean
_supported_statistics["Ack-weighted Mean"] = lambda trace, data: _stat_weighted_mean(trace, data,
        weight_field="Acks Received")
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

    def get_event_data(self, field_name, include_setup=False):
        events = self.get_events(include_setup)
        return [float(event[field_name]) for event in events]

    def get_statistic(self, field_name, statistic):
        if (statistic in _supported_statistics.keys()):
            return _supported_statistics[statistic](self, field_name)
        
        print("ERROR: Statistic \"%s\" is not yet implemented." % statistic)
        print("Supported statistics are %s" % str(_supported_statistics.keys()))
        return None
