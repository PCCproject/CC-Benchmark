import subprocess
import os
import test_utils

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

def check_idle(hostname, ip):
    check_idle_local = "/tmp/test_running"
    check_idle_remote = "/tmp/remote_test_running"
    res = subprocess.check_output(["ssh", "ocean0", "-t", "ssh", "pcc@"+str(ip),  "cat", check_idle_remote, check_idle_local])
    for rsp in res.split('\r\n')[:-1]:
        if rsp == "":
            break
        if not rsp.startswith('false'):
            return False
    return True

def get_remote_vm_ips(hostname):
    return_str = subprocess.check_output(["ssh", hostname, "\"\"arp -an\"\""]).decode("utf-8")
    lines = return_str.split("\n")
    virtual_lines = [l for l in lines if ("vir" in l and "incomplete" not in l)]

    addresses = []
    for line in virtual_lines:
        addr = get_address_from_arp_line(line)
        if addr not in test_utils.MANNUALLY_MAMANGED_VM_IPS:
            addresses.append(addr)

    aval_addr = []
    for ip in addresses:
        if check_idle(hostname, ip):
            aval_addr.append(ip)

    print("Available VM IP Addr are: " + str(aval_addr))
    return aval_addr

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
