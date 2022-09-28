import subprocess
import time
import os
import sys
import json
import psutil
import copy
import signal

from python_utils import vm_config
from python_utils.file_locations import free_vm_script
from python_utils.file_locations import occupy_vm_script
from python_utils.test_utils import read_test_list_to_list
from python_utils.test_utils import read_test_to_dict
from python_utils.test_utils import get_total_test_time
from python_utils.ssh_utils import get_idle_percent
from python_utils.ssh_utils import remote_call
from python_utils.ssh_utils import remote_copy
from python_utils.ssh_utils import remote_copyback
from python_utils.arg_helpers import arg_or_default
from python_utils import file_locations

MANUALLY_MANAGED_VM_NAMES = [
    "pcc_test_vm_2"
]

VIRSH_ENV_PREFIX = "LIBVIRT_DEFAULT_URI=qemu:///system"

def shutdown_vm_on_host(hostname, vm_name):
    subprocess.check_output(['ssh', hostname, VIRSH_ENV_PREFIX, 'virsh', 'shutdown', vm_name]) 

def boot_vm_on_host(hostname, vm_name):
    subprocess.check_output(['ssh', hostname, VIRSH_ENV_PREFIX, 'virsh', 'start', vm_name]) 

def get_vm_info_on_host(hostname):
    vm_info = []
    virsh_result = subprocess.check_output(['ssh', hostname, VIRSH_ENV_PREFIX, 'virsh', 'list', '--all']).decode('utf-8')
    lines = virsh_result.split("\n")

    vm_lines = lines[2:-2]

    for vm_line in vm_lines:
        vm_line_parts = vm_line.split(" ")
        vm_fields = []
        for vm_line_part in vm_line_parts:
            if not vm_line_part == "":
                vm_fields.append(vm_line_part)

        if ("pcc_test_vm" in vm_fields[1]):
            vm_info.append((vm_fields[1], vm_fields[2]))
    return vm_info

def check_idle_from_local(hostname, ip):
    vm_dir = file_locations.local_test_running_dir
    remote_dir = file_locations.remote_test_running_dir
    res = subprocess.check_output(["ssh", hostname, "-t", "ssh", "-o ",
        "\"StrictHostKeyChecking=no\"", "pcc@"+str(ip),  "cat", remote_dir, vm_dir]).decode("utf-8")
    print("Response: %s" % res)
    # print(res)
    for rsp in res.split('\r\n'):
        rsp = rsp.rstrip()
        # print("RES " + rsp)
        if (rsp == "") or ("known host" in rsp):
            continue

        rsp_list = rsp.split(" ")
        # print(rsp_list)
        if not rsp.startswith('false'):
            return float(rsp_list[1]) - (time.time() - float(rsp_list[2]))
    return 0

def get_vm_ip_from_name(hostname, vm_name):
    return_str = subprocess.check_output(["ssh", hostname, VIRSH_ENV_PREFIX, "virsh", "domifaddr", vm_name]).decode("utf-8")
    ip_line = return_str.split("\n")[2]
    ip_addr = ip_line.split(' ')[-1][:-3]
    return ip_addr

def get_remote_vm_ips(hostname, num_tests):
    addresses = {}

    ## Getting IP using VM_name(Used to automatically start/shutdown VMs)
    vm_info = get_vm_info_on_host(hostname)
    for (vm_name, vm_status) in vm_info:
        if (not vm_status == "running") or (vm_name in MANUALLY_MANAGED_VM_NAMES):
            continue
        
        addresses[vm_name] = get_vm_ip_from_name(hostname, vm_name)

    aval_addr = {}
    max_waittime = 0
    for name, ip in addresses.items():
        curr_waittime = check_idle_from_local(hostname, ip)
        if curr_waittime == 0:
            aval_addr[name] = ip
        else:
            if curr_waittime > max_waittime:
                max_waittime = curr_waittime

    print("Available VM IP Addr are: " + str(aval_addr))
    if num_tests > 0:
        while len(aval_addr) > num_tests:
            aval_addr.pop(list(aval_addr.keys())[-1])
    return aval_addr, max_waittime

def get_num_booted_vms_on_host(hostname):
    vm_info = get_vm_info_on_host(hostname)
    result = 0
    for (vm_name, vm_status) in vm_info:
        if vm_status == "running" and vm_name not in MANUALLY_MANAGED_VM_NAMES:
            result += 1
    return result

def boot_up_to_n_vms_on_host(hostname, n_vms_to_boot):
    print("Booting up to %d vms on %s" % (n_vms_to_boot, hostname))
    n_vms_booting = 0
    if (n_vms_to_boot <= 0):
        return 0

    vm_info = get_vm_info_on_host(hostname)
    for (vm_name, vm_status) in vm_info:
        print("VM status: %s" % vm_status)
        if (vm_name not in MANUALLY_MANAGED_VM_NAMES) and n_vms_to_boot > 0 and vm_status == "shut":
            boot_vm_on_host(hostname, vm_name)
            n_vms_to_boot -= 1
            n_vms_booting += 1

    return n_vms_booting

def boot_vms_if_needed(remote_hosts, list_of_tests_to_run):
    n_tests = len(list_of_tests_to_run)
    n_vms_up_or_booting = 0
    any_booting = False
    
    for hostname in remote_hosts:
        n_vms_up_or_booting += get_num_booted_vms_on_host(hostname)
    
    if (n_vms_up_or_booting > n_tests):
        print("Already have %d vms booted for %d tests, running immediately." % (n_vms_up_or_booting, n_tests))
        return

    for hostname in remote_hosts:
        n_booting = boot_up_to_n_vms_on_host(hostname, n_tests - n_vms_up_or_booting)
        if (n_booting > 0):
            any_booting = True
        n_vms_up_or_booting += n_booting

    if any_booting:
        print("VM(s) are booting up. Waiting for 30 seconds...")
        time.sleep(30)
