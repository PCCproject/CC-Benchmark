import subprocess
import os
import time

from python_utils import test_utils
from python_utils import file_locations

ocean0_web_dir = '/srv/shared/PCC/testing/pcc-web/test_data'
ocean0_res_dir = '/srv/shared/PCC/results'

def get_idle_percent(host):
    usage_str = subprocess.check_output(["ssh", host, "\"\"mpstat 1 1\"\""]).decode("utf-8")
    lines = str(usage_str).split("\n")
    vals = lines[-2].split(" ")
    idle_val = vals[-1]
    return float(idle_val)

def remote_call(host, cmd):
    local_cmd = "ssh %s \"%s\"" % (host, cmd)
    os.system(local_cmd)

def remote_copy(host, src, dst):
    local_cmd = "scp -r %s %s:%s" % (src, host, dst)
    os.system(local_cmd)

def remote_copyback(host, src, dst):
    local_cmd = "scp -r %s:%s %s" % (host, src, dst)
    os.system(local_cmd)

def get_address_from_arp_line(line):
    return (line.split('(')[1]).split(')')[0]

def cleanup_ssh_connections():

    # Find the root sshd processes by looking for processes listening on port 22.
    lines = subprocess.check_output(["sudo", "lsof", "-i", ":22"]).decode("utf-8").split("\n")
    listen_pids = []
    for line in lines:
        if ("LISTEN" in line):
            fields = [v for v in line.split(" ") if not v == ""]
            listen_pids.append(int(fields[1]))
    listen_pids = list(set(listen_pids))

    # Now, find all runnning sshd processes
    proc_lines = subprocess.check_output(["ps", "-aux"]).decode("utf-8").split("\n")
    sshd_pids = []
    for line in proc_lines:
        if ("/usr/sbin/sshd" in line):
            fields = [v for v in line.split(" ") if not v == ""]
            sshd_pids.append(int(fields[1]))

    for listen_pid in listen_pids:
        sshd_pids.remove(listen_pid)

    for sshd_pid in sshd_pids:
        os.system("sudo kill -9 %d" % sshd_pid)

def copy_back_to_ocean0(local_dir):
    local_dir = "/home/jaelee/PCC-Tester/results" + '/web'

    ocean0_web_dir = '/srv/shared/PCC/testing/pcc-web/test_data'
    ocean0_res_dir = '/srv/shared/PCC/results'
    for test in os.listdir(local_dir):
        test_path = local_dir + '/' + test
        if os.path.isdir(test_path):
            for date in os.listdir(test_path):
                data_path = test_path + '/' + date
                if os.path.isdir(data_path):
                    for file in os.listdir(data_path):
                        print(file)
