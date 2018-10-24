#!/usr/bin/python3
import multiprocessing
import queue
import subprocess
import time
import os
import sys
import json

local_testing_dir = "/home/njay2/PCC/testing/"
local_results_dir = local_testing_dir + "results/"
remote_testing_dir = "/home/njay2/PCC/testing/"
remote_username = "njay2"
remote_hosts = {
    "localhost":local_testing_dir
}

def get_idle_percent(host):
    usage_str = subprocess.check_output(["ssh", host, "\"\"mpstat 1 1\"\""]).decode("utf-8")
    lines = str(usage_str).split("\n")
    vals = lines[-2].split(" ")
    idle_val = vals[-1]
    return float(idle_val)

def remote_call(host, cmd):
    local_cmd = "ssh %s@%s \"%s\"" % (remote_username, host, cmd)
    #print(local_cmd)
    os.system(local_cmd)

def remote_copy(host, src, dst):
    local_cmd = "scp -r %s %s@%s:%s" % (src, remote_username, host, dst)
    os.system(local_cmd)

def remote_copyback(host, src, dst):
    local_cmd = "scp -r %s@%s:%s %s" % (remote_username, host, src, dst)
    os.system(local_cmd)

def setup_remote_testing_dir(host, remote_dir):
    remote_call(host, "mkdir -p %s" % remote_dir)
    #remote_copy(host, local_testing_dir + "*", remote_dir)

def get_address_from_arp_line(line):
    return (line.split('(')[1]).split(')')[0]

def get_remote_vm_ips(hostname):
    return_str = subprocess.check_output(["ssh", hostname, "\"\"arp -an\"\""]).decode("utf-8")
    lines = return_str.split("\n")
    virtual_lines = [line for line in lines if "vir" in line]
    addresses = [get_address_from_arp_line(line) for line in virtual_lines]
    return addresses 

class RemoteVmManager:
    def __init__(self, hostname, remote_testing_dir, vm_ip):
        print("Creating VM manager for %s:%s" % (hostname, vm_ip))
        self.test_in_progress = False
        self.hostname = hostname
        self.remote_testing_dir = remote_testing_dir
        self.vm_ip = vm_ip
        self.vm_test_queue = multiprocessing.Queue()
        self.busy = multiprocessing.Value('i', 0)
        self.done_queue = multiprocessing.Queue()
        self.kill_queue = multiprocessing.Queue()
        self.proc = multiprocessing.Process(target=self.run_manager, args=(self.vm_test_queue,
            self.done_queue, self.kill_queue))
        self.proc.start()

    def set_busy(self, flag):
        if flag:
            self.busy.value = 1
        else:
            self.busy.value = 0

    def busy_or_test_queued(self):
        print("busy = %d, vm_test_queue.empty = %s" % (self.busy.value, str(self.vm_test_queue.empty())))
        return (self.busy.value == 1) or (not self.vm_test_queue.empty())

    def run_next_test(self, test_name, test_scheme):
        cmd = "%s %s %s %s" % (os.path.join(self.remote_testing_dir, "run_vm_test.py"),
            self.vm_ip, test_scheme, test_name)
        remote_call(self.hostname, cmd)
        self.test_in_progress = False

    def run_manager(self, test_queue, done_queue, kill_queue):
        done = False
        while (not done):
            print("Manager %s checking for jobs" % self.get_id_string())
            try:
                self.set_busy(True)
                next_test, next_scheme = test_queue.get_nowait()
                print("Manager %s found a job" % self.get_id_string())
                self.run_next_test(next_test, next_scheme)
            except queue.Empty as e:
                print("No test in queue...")
            self.set_busy(False)
            time.sleep(1)
            done = (not done_queue.empty())
        print("Manager %s shutting down" % self.get_id_string())

    def get_id_string(self):
        return "%s:%s" % (self.hostname, self.vm_ip)

class RemoteHostManager:
    def __init__(self, hostname, testing_dir, test_queue):
        self.hostname = hostname
        self.testing_dir = testing_dir
        self.test_in_progress = False
        self.done_queue = multiprocessing.Queue()
        self.kill_queue = multiprocessing.Queue()
        self.remote_vm_managers = []
        self.init_remote_vm_managers()
        self.proc = multiprocessing.Process(target=self.run_manager, args=(test_queue, self.done_queue, self.kill_queue))
        self.proc.start()

    def init_remote_vm_managers(self):
        vm_ips = get_remote_vm_ips(self.hostname)
        for vm_ip in vm_ips:
            self.remote_vm_managers.append(RemoteVmManager(self.hostname, self.testing_dir,
                vm_ip))

    def test_in_progress(self):
        return self.test_in_progress

    def run_next_test(self):
        test_in_progress = True
        test_name = test_queue.get()
        print("Running test %s" % test_name)
        cmd = "%s %s %s" % (os.path.join(self.testing_dir, "run_vm_test.py"),
            sys.argv[1], test_name)
        print("Remote call: %s" % cmd)
        remote_call(hostname, cmd)
        print("Copying results back...")
        remote_copyback(hostname, os.path.join(self.testing_dir, "results", "*"),
            os.path.join(local_testing_dir, "results"))

    def cleanup_remote_vm_managers(self):
        for vm_manager in self.remote_vm_managers:
            vm_manager.done_queue.put(True)

    def run_manager(self, test_queue, done_queue, kill_queue):
        done = False

        print("Running manager for host %s" % self.hostname)
        while (not done):
            time.sleep(2)
            vms_busy = 0
            free_cpu = get_idle_percent(self.hostname)
            for vm_manager in self.remote_vm_managers:
                print("Checking if VM manager %s is busy..." % vm_manager.get_id_string())
                if vm_manager.busy_or_test_queued():
                    print("\tVM manager busy")
                    vms_busy += 1
                elif (not test_queue.empty()):
                    print("Assigning test to %s" % vm_manager.get_id_string())
                    vm_manager.vm_test_queue.put(test_queue.get())
                    vms_busy += 1
            print("Host %s has %f CPU time free" % (self.hostname, free_cpu))
            done = test_queue.empty() and (vms_busy == 0)

        print("Manager for %s done" % self.hostname)
        self.cleanup_remote_vm_managers()
        remote_copyback(self.hostname, "/tmp/pcc_automated_testing/results/*", local_results_dir)
        remote_call(self.hostname, "rm -rf /tmp/pcc_automated_testing/results/")

test_queue = multiprocessing.Queue()
test_file = os.path.join(local_testing_dir, "tests", sys.argv[2]) + ".json"
test_json = None
with open(test_file) as f:
    test_json = json.load(f)
print("Loaded test (list) from %s" % test_file)

test_filenames = []
if "Tests" in test_json.keys():
    test_filenames = test_json["Tests"]
else:
    test_filenames = [sys.argv[2]]

for test_filename in test_filenames:
    test_queue.put((test_filename, sys.argv[1]))

host_managers = []
for hostname in remote_hosts.keys():
    print("Creating host manager for %s" % hostname)
    host_managers.append(RemoteHostManager(hostname, remote_hosts[hostname], test_queue))

##
#   Load in the test descriptor files.
##

for manager in host_managers:
    manager.proc.join()
