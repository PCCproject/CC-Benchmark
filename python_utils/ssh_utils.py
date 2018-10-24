import subprocess
import os

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

def get_remote_vm_ips(hostname):
    return_str = subprocess.check_output(["ssh", hostname, "\"\"arp -an\"\""]).decode("utf-8")
    lines = return_str.split("\n")
    virtual_lines = [line for line in lines if "vir" in line]
    addresses = [get_address_from_arp_line(line) for line in virtual_lines]
    return addresses 
