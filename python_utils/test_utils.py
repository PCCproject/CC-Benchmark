from python_utils import file_locations
import json
import os

def read_topology_to_dict(topology_name):
    topo_file = os.path.join(file_locations.topos_dir, topology_name + ".json")
    topo_json = None
    with open(topo_file) as f:
        topo_json = json.load(f)
    return topo_json
