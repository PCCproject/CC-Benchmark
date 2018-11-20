import json
import os
import numpy as np

_supported_statistics = {}

def _stat_mean(data):
    return np.mean(data)

_supported_statistics["Mean"] = _stat_mean

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
        return [float(event[field_name]) for event in self.get_events(include_setup)]

    def get_statistic(self, field_name, statistic, include_setup=False):
        if (statistic in _supported_statistics.keys()):
            return _supported_statistics[statistic](self.get_event_data(field_name, include_setup))
        
        print("ERROR: Statistic \"%s\" is not yet implemented." % statistic)
        print("Supported statistics are %s" % str(_supported_statistics.keys()))
        return None
