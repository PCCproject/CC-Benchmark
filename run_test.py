#!/usr/bin/python3
import os
from python_utils import file_locations
from python_utils import test_utils
from python_utils import pantheon_setup
from python_utils import github_utils
from python_utils import ssh_utils
from python_utils.test_utils import read_topology_to_dict
from python_utils.test_utils import read_test_list_to_list
from python_utils.test_utils import read_test_to_dict
from python_utils.test_utils import get_total_test_time
from python_utils.test_utils import clear_testfile_and_exit
from python_utils.test_utils import get_num_trial
from python_utils.pantheon_log_conversion import convert_pantheon_log
import python_utils.calculate_metrics as calculate_metrics
import traceback
import subprocess
import sys
import time
import json
import datetime
import random
import signal
mininet_dir = "/home/pcc/mininet/"
sys.path.append(mininet_dir)
from python_utils import mininet_utils
from python_utils import arg_helpers
from mininet.link import TCLink
from mininet.net import Mininet

from pprint import pprint
results_dir = None
default_build_dir = "/home/pcc/pcc_test_scheme/"
scheme_to_test = sys.argv[1]
tests_to_run = sys.argv[2]

# Catch sigint to clear run_test file
signal.signal(signal.SIGINT, clear_testfile_and_exit)

if "--is-remote" not in sys.argv:
    # run_remote_test should have checked first if the this vm is idle
    vm_busy = test_utils.get_wait_time_from_VM()
    if (vm_busy != 0):
        print("VM is currently busy")
        if vm_busy < 0: #might happen due to synchonize issue
            print("Almost Done Testing... Try again later")
        else:
            print("Approximately {} seconds remaining...".format(vm_busy))

        os._exit(0)
    else:
        test_list = read_test_list_to_list(tests_to_run)
        test_dur = get_total_test_time(test_list, 1)
        print(test_dur)

        with open(file_locations.local_test_running_dir, 'w') as f:
            f.write("true {} {}\r\n".format(test_dur, time.time()))

remote_test = '--is-remote' in sys.argv
print("Remote Test {}".format(remote_test))

default_bw = 30
default_lat = 30

is_git_repo = False
git_repo = None
git_branch = None
git_checksum = None

scheme_nickname = arg_helpers.arg_or_default("--nickname", None)

web_result = False
for args in sys.argv:
    if 'web-result' in args or 'web_result' in args:
        web_result = True

print('web_result ' + str(web_result))
mptcp = "mptcp" in sys.argv[2]

# This means we are testing a branch from a repository -- we probably have to build it first
if (":" in scheme_to_test):
    is_git_repo = True
    parts = scheme_to_test.split(":")
    repo_name = parts[0]
    branch = parts[1]

    # Check if a repo exists in the usual build location
    if (os.path.isdir(os.path.join(default_build_dir, ".git"))):

        # We have a build dir, but we may not have the correct repo or branch.
        if (not github_utils.dir_has_repo(repo_name, branch, default_build_dir)):
            git_checksum = github_utils.build_repo_in_dir(repo_name, branch, default_build_dir)
        else:
            git_checksum = github_utils.get_repo_checksum(default_build_dir)
    else:
        # No dir? Make it and clone there
        os.system("mkdir -p %s" % default_build_dir)
        git_checksum = github_utils.build_repo_in_dir(repo_name, branch, default_build_dir)

    repo = github_utils.BuildableRepo.get_by_short_name(repo_name)
    scheme_to_test = os.path.join(default_build_dir, repo.src_dir)

    git_repo = repo_name
    git_branch = branch

extra_args = arg_helpers.arg_or_default("--extra-args", None)
if extra_args is not None:
    extra_args = extra_args.split(',')

if (scheme_to_test not in test_utils.SUPPORTED_PANTHEON_SCHEMES):
    scheme_to_test = pantheon_setup.add_scheme_to_pantheon(scheme_to_test, extra_args)

data_dir = "/tmp/pcc_automated_testing/data/"
username = "pcc"

def sort_by_start_time(flows):
    for flow in flows:
        if "start" not in flow.keys():
            flow["start"] = 0.0

    return sorted(flows, key=lambda k: k["start"])

def get_free_run_id():
    return random.randint(0, 2e9)

def wait_for_all_logs_or_timeout(log_names, timeout):
    next_log_to_check = 0
    start_wait_time = time.time()
    time_waited = 0.0
    while time_waited < timeout and next_log_to_check < len(log_names):
        waiting_for_file = False
        while next_log_to_check < len(log_names) and not waiting_for_file:
            if os.path.exists(log_names[next_log_to_check]):
                next_log_to_check += 1
            else:
                waiting_for_file = True
        time.sleep(1.0)
        time_waited = time.time() - start_wait_time
    if next_log_to_check < len(log_names):
        return False
    return True

def run_test(test_dict):
    global remote_test
    date_string = datetime.date.today().strftime("%B_%d_%Y") + "_%d" % (int(round(time.time() * 1000)))
    if remote_test:
        results_dir = os.path.join(file_locations.results_dir, 'remote', test["Name"], date_string)
    else:
        results_dir = os.path.join(file_locations.results_dir, test["Name"], date_string)

    print(results_dir)


    os.system("mkdir -p %s" % results_dir)
    print("Removing any running mininet instance.")
    mininet_clean_output = subprocess.check_output(["sudo", "mn", "-c"])
    test_topo_dict = read_topology_to_dict(test_dict["Topology"])
    test_link_types = test_dict["Link Types"]
    topo = mininet_utils.MyTopo(test_topo_dict, test_link_types)
    net = Mininet(topo=topo, link=TCLink)


    if mptcp:
        h1 = net.getNodeByName("h1")
        h2 = net.getNodeByName("h2")
        # hard code configuration for simple mptcp topology
        os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh')
        os.system('sysctl -w net.mptcp.mptcp_scheduler=default')
        os.system('sysctl -w net.mptcp.mptcp_enabled=1')

        # configure 2 different interfaces
        h1_cmd1 = 'ifconfig h1-eth0 10.0.0.1'
        h1_cmd2 = 'ifconfig h1-eth1 10.0.1.1'
        h2_cmd1 = 'ifconfig h2-eth0 10.0.0.2'
        h2_cmd2 = 'ifconfig h2-eth1 10.0.1.2'

        print("{}\n{}\n{}\n{}".format(h1_cmd1, h1_cmd2, h2_cmd1, h2_cmd2))
        h1.cmd(h1_cmd1)
        h1.cmd(h1_cmd2)
        h2.cmd(h2_cmd1)
        h2.cmd(h2_cmd2)

        # Create two different routing tables for each source address
        h1_cmd1 = 'ip rule add from 10.0.0.1 table 1'
        h1_cmd2 = 'ip rule add from 10.0.1.1 table 2'
        h2_cmd1 = 'ip rule add from 10.0.0.2 table 1'
        h2_cmd2 = 'ip rule add from 10.0.1.2 table 2'

        print("{}\n{}\n{}\n{}".format(h1_cmd1, h1_cmd2, h2_cmd1, h2_cmd2))
        h1.cmd(h1_cmd1)
        h1.cmd(h1_cmd2)
        h2.cmd(h2_cmd1)
        h2.cmd(h2_cmd2)

        # Configure two different routing tables
        h1_cmd1 = 'ip route add 10.0.0.0/24 dev h1-eth0 scope link table 1'
        h1_cmd2 = 'ip route add 10.0.1.0/24 dev h1-eth1 scope link table 2'
        h2_cmd1 = 'ip route add 10.0.0.0/24 dev h2-eth0 scope link table 1'
        h2_cmd2 = 'ip route add 10.0.1.0/24 dev h2-eth1 scope link table 2'

        print("{}\n{}\n{}\n{}".format(h1_cmd1, h1_cmd2, h2_cmd1, h2_cmd2))
        h1.cmd(h1_cmd1)
        h1.cmd(h1_cmd2)
        h2.cmd(h2_cmd1)
        h2.cmd(h2_cmd2)

        h1_cmd1 = 'ip route add default via 10.0.0.1 dev eth0 table 1'
        h1_cmd2 = 'ip route add default via 10.0.1.1 dev eth1 table 2'
        h2_cmd1 = 'ip route add default via 10.0.0.2 dev eth0 table 1'
        h2_cmd2 = 'ip route add default via 10.0.1.2 dev eth1 table 2'

        print("{}\n{}\n{}\n{}".format(h1_cmd1, h1_cmd2, h2_cmd1, h2_cmd2))
        h1.cmd(h1_cmd1)
        h1.cmd(h1_cmd2)
        h2.cmd(h2_cmd1)
        h2.cmd(h2_cmd2)

        print(h1.cmd('ip rule show'))
        print(h2.cmd('ip rule show'))

        print(h1.cmd('ip route'))
        print(h2.cmd('ip route'))

        print(h1.cmd('ip route show table 1'))
        print(h2.cmd('ip route show table 1'))
        print(h1.cmd('ip route show table 2'))
        print(h2.cmd('ip route show table 2'))

        print(h1.cmd('ifconfig'))
        print(h2.cmd('ifconfig'))
    mininet_utils.sshd(net)

    # time.sleep(500)

    topo.start_all_link_managers(net)
    flows = sort_by_start_time(test_dict["Flows"])
    run_ids = {}
    max_end = 0
    time_offset = time.time()
    for i in range(0, len(flows)):
        flow = flows[i]
        run_id = run_ids[i] = get_free_run_id()
        if flow["protocol"] == "TEST":
            flow["protocol"] = scheme_to_test
        run_dur = 30
        if ("dur" in flow.keys()):
            run_dur = flow["dur"]
        run_end = flow["start"] + run_dur
        if (run_end > max_end):
            max_end = run_end
        sleep_dur = flow["start"] + time_offset - time.time()
        if (sleep_dur > 0.0):
            time.sleep(sleep_dur)
        test_command = "%s/test/test.py remote -t %d --start-run-id %d --data-dir %s --schemes %s %s:%s" % (file_locations.pantheon_dir, run_dur, run_id, data_dir,
            flow["protocol"], flow["dst"], file_locations.pantheon_dir)

        cmd = "sudo -u %s ssh -i ~/.ssh/id_mininet_rsa %s \"%s\" &" % (username, flow["src"], test_command)
        # if mptcp:
        #     if flow['src'][-3] == '0':
        #         cmd = "sudo -u %s ssh -i ~/.ssh/id_mininet_rsa %s \"%s\" &" % (username, '10.0.0.1', test_command)
        #     else:
        #         cmd = "sudo -u pcc ssh -i ~/.ssh/id_mininet_rsa 10.0.0.1 -t ssh %s \"%s\" &" % (flow['src'], test_command)
        # else:
        #     cmd = "sudo -u %s ssh -i ~/.ssh/id_mininet_rsa %s \"%s\" &" % (username, flow["src"], test_command)

        print("\t\tCMD IS", cmd)
        os.system(cmd)

    timeout = 400.0 + max_end + time_offset - time.time()
    all_log_names = ["%s/%s_datalink_run%d.log" % (data_dir, flows[i]["protocol"], run_ids[i]) for i in range(0, len(flows))]
    all_logs_finished = wait_for_all_logs_or_timeout(all_log_names, timeout)

    topo.stop_all_link_managers()
    net.stop()

    if not all_logs_finished:
        sys.stderr.write("(PCC Tester) ERROR: test run did not create all expected log files.")

    for i in range(0, len(flows)):
        date_string_split = date_string.split('_')
        date_string_split[-1] = date_string_split[-1][-5:]
        date_string = '_'.join(date_string_split)
        flow = flows[i]
        run_id = run_ids[i]
        log_name = "%s/%s_datalink_run%d.log" % (data_dir, flow["protocol"], run_id)
        saved_name = "%s/%s_datalink.%s.log" % (results_dir, flow["protocol"], flow["name"])
        converted_name = "%s/%s.%s.json" % (results_dir, flow["protocol"], flow["name"])
        print("Copying pantheon log.")
        time.sleep(2)
        os.system("cp %s %s" % (log_name, saved_name))
        time.sleep(2)
        print("Pantheon log copied...")
        worked = False
        n_tries = 0
        while (not worked) and (n_tries < 2):
            n_tries += 1
            try:
                print("Beginning log conversion...")
                convert_pantheon_log(log_name, converted_name)
                print("Finished log conversion...")
                worked = True
            except Exception as e:
                print(e, file=sys.stderr)
                traceback.print_exc()

        if not worked:
            print("ERROR: Could not convert pantheon log", file=sys.stderr)
            exit(-1)

    scheme_name = scheme_to_test
    if scheme_nickname is not None:
        scheme_name = scheme_nickname
    metadata = {
        "Scheme":scheme_name,
        "Finish Time":int(round(time.time() * 1000))
    }
    if is_git_repo:
        metadata["Repo"] = git_repo
        metadata["Branch"] = git_branch
        metadata["Checksum"] = git_checksum
    if extra_args is not None:
        metadata["PCC Args"] = []
        for extra_arg in extra_args:
            metadata["PCC Args"].append(extra_arg)
    with open(os.path.join(results_dir, "test_metadata.json"), "w") as f:
        json.dump(metadata, f)

    if web_result:
        if is_git_repo:
            scheme_name = '{},{},{}'.format(metadata["Repo"], metadata["Branch"], metadata["Checksum"][-5:]).replace('-', '_')

        print("Saving test results to pcc-web directory...")
        # web_dir = '/home/pcc/PCC/testing/pcc-web/test_data/'
        test_split = test["Name"].split('.')
        testname = test_split[0] + '_test'
        if len(test_split) > 1:
            detail = '.'.join(test_split[1:])
        else:
            detail = testname

        filename = test['Name']

        test_dir = data_dir + testname + '/data/' + scheme_name + '/'
        num_trial = get_num_trial(test_dir, detail)

        filename = "{}/{}-{}-datapoints-{}-{}.json".format(results_dir, testname, scheme_name, detail, date_string)
        metric_filename = "{}/{}-{}-metric-{}-{}.json".format(results_dir, testname, scheme_name, detail, date_string)
        os.system('mkdir -p {}'.format(results_dir))
        try:
            os.system('chmod -R 777 {}'.format(results_dir))
        except:
            # Do nothing
            pass

        print(filename)

        metric = {}
        datapoints = {}
        meanThrput = []

        split = detail.split('_to_')
        bw = [default_bw] * len(flows)
        lat = [default_lat] * len(flows)
        loss = [0] * len(flows)
        if 'mbps' in split[0]:
            for i, sp in enumerate(split):
                bw[i] = int(sp.split('mbps')[0])

        if 'ms' in split[0]:
            for i, sp in enumerate(split):
                lat[i] = int(sp.split('ms')[0])

        if 'loss' in split[0]:
            for i, sp in enumerate(split):
                loss[i] = float(sp.split('loss')[0])

        for i in range(0, len(flows)):
            flow = flows[i]
            orig_data = "%s/%s.%s_orig.json" % (results_dir, flow["protocol"], flow["name"])
            merged_data = "%s/%s.%s.json" % (results_dir, flow["protocol"], flow["name"])
            with open(orig_data) as f:
                data = json.load(f)

            with open(merged_data) as f:
                merged_data = json.load(f)

            points, thrput = calculate_metrics.getTimeThrputFromJson(merged_data)

            datapoints['flow{}'.format(i+1)] = points
            meanThrput.append(thrput)

            flow_protocol = flow["protocol"]
            if flow_protocol == 'pcc_test_scheme':
                flow_protocol = scheme

            if flow_protocol not in metric:
                metric[flow_protocol] = {}

            metric[flow_protocol]['flow{}'.format(i+1)] = calculate_metrics.getMetricScore(data, bw[i], lat[i], loss[i])

            datapoints['flow{} lat'.format(i+1)] = lat[i]
            datapoints['flow{} bw'.format(i+1)] = bw[i]

        if len(flows) > 1:
            if testname.startswith('rtt_fairness'):
                datapoints['Ratio'] = datapoints['flow2 lat'] / datapoints['flow1 lat']
            datapoints["Jain idx"] = calculate_metrics.getJainIndex(meanThrput)

        with open(metric_filename, 'w') as f:
            f.write(json.dumps(metric, indent=4))

        with open(filename, 'w') as f:
            f.write(json.dumps(datapoints, indent=4))

    os.system("rm -rf %s/*" % data_dir)

os.system("/home/pcc/PCC/testing/pantheon/test/setup.py --schemes {}".format(scheme_to_test))

##
#   Load in the test descriptor files.
##

all_test_names = read_test_list_to_list(tests_to_run)
all_tests = [read_test_to_dict(t) for t in all_test_names]

##
#   Begin executing tests. Note: Eventually tests should be grouped by topology so
#   each test doesn't require a restart of mininet, and so tests can be scheduled
#   better.
##

try:
    for test in all_tests:
        run_test(test)
except Exception as e:
    print(e)
    traceback.print_exc()

if "--is-remote" in sys.argv:
    ssh_utils.cleanup_ssh_connections()
    os.system("sudo killall ssh")
else:
    clear_testfile_and_exit()

if remote_test:
    os.system('rm -rf {}'.format(results_dir))
