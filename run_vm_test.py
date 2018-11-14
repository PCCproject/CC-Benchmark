#!/usr/bin/python3
import sys
import os

vm_ip = sys.argv[1]
vm_cmd = "sudo /home/pcc/PCC/testing/run_test.py"
vm_test_scheme = sys.argv[2]
vm_test = sys.argv[3]
vm_results_dir = "/home/pcc/PCC/testing/results/"
local_results_dir = "/tmp/pcc_automated_testing/results/"
enable_forwarding_command = "sudo sysctl -w net.ipv4.ip_forward=1"

os.system("ssh pcc@%s \"%s\"" % (vm_ip, enable_forwarding_command))
os.system("ssh pcc@%s \"%s %s %s --is-remote\"" % (vm_ip, vm_cmd, vm_test_scheme, vm_test))
os.system("mkdir -p %s" % local_results_dir)
os.system("scp -r pcc@%s:%s/* %s" % (vm_ip, vm_results_dir, local_results_dir))
os.system("ssh pcc@%s \"sudo rm -rf %s/*\"" % (vm_ip, vm_results_dir))
os.system("ssh pcc@%s \"killall python\"" % vm_ip)
