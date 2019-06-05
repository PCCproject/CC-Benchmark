#!/usr/bin/python3
import multiprocessing
import queue
import subprocess
import time
import os
import sys
import json
import psutil
from python_utils import vm_config
from python_utils.test_utils import read_test_list_to_list
from python_utils.test_utils import read_test_to_dict
from python_utils.ssh_utils import get_idle_percent
from python_utils.ssh_utils import remote_call
from python_utils.ssh_utils import remote_copy
from python_utils.ssh_utils import remote_copyback
from python_utils.ssh_utils import get_remote_vm_ips
from python_utils.arg_helpers import arg_or_default

from graphing.analysis.results_library import ResultsLibrary
from graphing.utils import data_utils
from python_utils.file_locations import results_dir

results_lib = ResultsLibrary(results_dir)

#local_testing_dir = "/home/njay2/PCC/testing/"
local_testing_dir = "/home/jaelee/PCC-Tester/"
local_results_dir = local_testing_dir + "results/"
#remote_testing_dir = "/home/njay2/PCC/testing/"
remote_testing_dir = "/home/jaelee/PCC-Tester/"
remote_hosts = {
    "ocean0":remote_testing_dir
}

tests_to_run = sys.argv[2]
schemes_to_test = sys.argv[1].split(" ")
replicas = 1
if (len(sys.argv) > 3):
    replicas = int(sys.argv[3])

EXTRA_ARGS = arg_or_default("--extra-args", default="")

class RemoteVmManager:
    def __init__(self, hostname, remote_testing_dir, vm_ip):
        print("Creating VM manager for %s:%s" % (hostname, vm_ip))
        self.has_run_test = False
        self.hostname = hostname
        self.remote_testing_dir = remote_testing_dir
        self.vm_ip = vm_ip
        self.vm_test_queue = multiprocessing.Queue()
        self.busy = multiprocessing.Value('i', 0)
        self.done_queue = multiprocessing.Queue()
        self.error_queue = multiprocessing.Queue()
        self.proc = multiprocessing.Process(target=self.run_manager, args=(self.vm_test_queue,
            self.done_queue, self.error_queue))
        self.proc.start()
        self.cur_test = None
        self.child_pid = self.proc.pid

    def run_on_vm_host(self, cmd):
        remote_call(self.hostname, cmd)

    def run_on_vm(self, cmd):
        remote_cmd = "ssh pcc@%s '%s'" % (self.vm_ip, cmd)
        remote_call(self.hostname, remote_cmd)

    def is_up(self):
        return (self.proc.exitcode is None) and psutil.pid_exists(self.child_pid)
        #return self.proc.is_alive() # Why doesn't this work?

    def restart_proc(self):
        if self.proc is not None:
            self.proc.terminate()
        self.proc = multiprocessing.Process(target=self.run_manager, args=(self.vm_test_queue,
            self.done_queue, self.error_queue))
        self.proc.start()
        self.child_pid = self.proc.pid
        self.set_busy(False)

    def assign_test(self, test):
        self.cur_test = test
        self.vm_test_queue.put(test)

    def set_busy(self, flag):
        if flag:
            self.busy.value = 1
        else:
            self.busy.value = 0

    def busy_or_test_queued(self):
        return (self.busy.value == 1) or (not self.vm_test_queue.empty())

    def run_first_test_setup(self):
        try:
            self.run_on_vm_host("mkdir -p %s" % vm_config.host_results_dir)
        except Exception as e:
            print(e)
            os._exit(1)
        if "--pull-repo" in sys.argv:
            self.run_on_vm("%s/pull_this_repo.py" % vm_config.testing_dir)
        self.run_on_vm("sudo sysctl -w net.ipv4.ip_forward=1")

    def run_next_test(self, test_name, test_scheme):
        if not self.has_run_test:
            self.run_first_test_setup()
            self.has_run_test = True
        self.run_on_vm('sudo %s %s %s --is-remote --extra-args=%s' % (vm_config.run_test_cmd, test_scheme,
            test_name, EXTRA_ARGS))
        self.run_on_vm_host("scp -r pcc@%s:%s/* %s" % (self.vm_ip, vm_config.vm_results_dir,
            vm_config.host_results_dir))
        self.run_on_vm("sudo rm -rf %s" % (vm_config.vm_results_dir))
        self.run_on_vm("sudo killall python")

    def run_manager(self, test_queue, done_queue, error_queue):
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
        #vm_ips = ["192.168.122.35", "192.168.122.22", "192.168.122.24", "192.168.122.25"]
        #vm_ips = ["192.168.122.35"]
        vm_ips = get_remote_vm_ips(self.hostname)
        for vm_ip in vm_ips:
            self.remote_vm_managers.append(RemoteVmManager(self.hostname, self.testing_dir,
                vm_ip))

    def cleanup_remote_vm_managers(self):
        for vm_manager in self.remote_vm_managers:
            vm_manager.done_queue.put(True)

    def run_manager(self, test_queue, done_queue, kill_queue):
        done = False
        busy_start = {}

        print("Running manager for host %s" % self.hostname)
        while (not done):
            time.sleep(2)
            vms_busy = 0
            for vm_manager in self.remote_vm_managers:
                if not vm_manager.is_up():
                    print("***********************************************")
                    print("Restarting dead VM at %s" % vm_manager.get_id_string())
                    print("***********************************************")
                    test_queue.put(vm_manager.cur_test)
                    vm_manager.restart_proc()
                    vms_busy += 1
                elif vm_manager.busy_or_test_queued():
                    vms_busy += 1
                    busy_time = time.time() - busy_start[vm_manager.get_id_string()]
                    print("VM manager %s busy for %.2fs" % (vm_manager.get_id_string(), busy_time))
                    if busy_time > 500.0:
                        print("***********************************************")
                        print("Restarting stalled VM at %s" % vm_manager.get_id_string())
                        print("***********************************************")
                        test_queue.put(vm_manager.cur_test)
                        vm_manager.restart_proc()
                elif (not test_queue.empty()):
                    if (get_idle_percent(self.hostname) > 25):
                        print("Tests remaining: %d" % test_queue.qsize())
                        vm_manager.assign_test(test_queue.get())
                        busy_start[vm_manager.get_id_string()] = time.time()
                        time.sleep(1)
                        vms_busy += 1
                    else:
                        print("Host %s is too busy." % self.hostname)
            done = test_queue.empty() and (vms_busy == 0)

        print("Manager for %s done" % self.hostname)
        self.cleanup_remote_vm_managers()
        remote_copyback(self.hostname, vm_config.host_results_dir + "*", local_results_dir)
        remote_call(self.hostname, "rm -rf " + vm_config.host_results_dir)


##
#   Read in a list of all tests to run, and enqueue them for the VMs to run.
##

test_queue = multiprocessing.Queue()
for scheme_to_test in schemes_to_test:
    for test_name in read_test_list_to_list(tests_to_run):
        n_tests_done = results_lib.get_num_tests_done(test_name, scheme_to_test)
        print("Have %d tests for %s:%s, need %d more" % (n_tests_done, test_name, scheme_to_test, replicas - n_tests_done))
        for i in range(0, replicas - n_tests_done):
            test_queue.put((test_name, scheme_to_test))

print("Preparing to run %d tests" % test_queue.qsize())
time.sleep(2.0)

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
