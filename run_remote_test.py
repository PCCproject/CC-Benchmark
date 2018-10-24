#!/usr/bin/python3
import multiprocessing
import queue
import subprocess
import time
import os
import sys
import json
from python_utils.test_utils import read_test_list_to_list
from python_utils.test_utils import read_test_to_dict
from python_utils.ssh_utils import get_idle_percent
from python_utils.ssh_utils import remote_call
from python_utils.ssh_utils import remote_copy
from python_utils.ssh_utils import remote_copyback
from python_utils.ssh_utils import get_remote_vm_ips

local_testing_dir = "/home/njay2/PCC/testing/"
local_results_dir = local_testing_dir + "results/"
remote_testing_dir = "/home/njay2/PCC/testing/"
remote_hosts = {
    "localhost":local_testing_dir
}

tests_to_run = sys.argv[2]
scheme_to_test = sys.argv[1]

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
        return (self.busy.value == 1) or (not self.vm_test_queue.empty())

    def run_next_test(self, test_name, test_scheme):
        cmd = "%s %s %s %s" % (os.path.join(self.remote_testing_dir, "run_vm_test.py"),
            self.vm_ip, test_scheme, test_name)
        remote_call(self.hostname, cmd)
        self.test_in_progress = False

    def run_manager(self, test_queue, done_queue, kill_queue):
        done = False
        while (not done):
            try:
                self.set_busy(True)
                next_test, next_scheme = test_queue.get_nowait()
                self.run_next_test(next_test, next_scheme)
            except queue.Empty as e:
                pass
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
                if vm_manager.busy_or_test_queued():
                    vms_busy += 1
                elif (not test_queue.empty()):
                    vm_manager.vm_test_queue.put(test_queue.get())
                    vms_busy += 1
            done = test_queue.empty() and (vms_busy == 0)

        print("Manager for %s done" % self.hostname)
        self.cleanup_remote_vm_managers()
        remote_copyback(self.hostname, "/tmp/pcc_automated_testing/results/*", local_results_dir)
        remote_call(self.hostname, "rm -rf /tmp/pcc_automated_testing/results/")


##
#   Read in a list of all tests to run, and enqueue them for the VMs to run.
##

test_queue = multiprocessing.Queue()
for test_name in read_test_list_to_list(tests_to_run):
    test_queue.put((test_name, scheme_to_test))

##
#   Start the test-running managers for remote machines and VMs.
##

host_managers = []
for hostname in remote_hosts.keys():
    print("Creating host manager for %s" % hostname)
    host_managers.append(RemoteHostManager(hostname, remote_hosts[hostname], test_queue))

##
#   Now, we wait until all managers have finished.
##

for manager in host_managers:
    manager.proc.join()
