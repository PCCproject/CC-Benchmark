# PCC-Tester

A (prototype) push-button testing environment for congestion control.

## Installation

Scripts not yet available.

To run the PCC-Tester, you must:
1. Run a version of the pcc_tester VM (acct: pcc, password: pcc) either locally or remotely. It's about 8GB, so it doesn't seem wise to put it on the git repo.
2. Copy "run_vm_test.py" to the machine with your pcc_tester VM on it.
3. Point "run_remote_test.py" to the location of run_vm_test.py on a remote machine (needs hostname and directory).
4. Update "run_remote_test.py" to reflect your choice of local results directory.
5. Install any missing python3 packages that we used. Until we get a script, the easiest way to find these is just to
run "run_remote_test.py" and see what it tries to import.

Installation TODOs (in no particular order):
1. Try to gather all reasonably sized dependencies into the VM image, so most people can use the same image.
2. Create scripts for all necessary python packages.
3. Load information about remote hosts and local directories from a config script.

## Usage

### Running the tests
You can run a simple test of a version on the PCC master branch by running:
"./run_remote_test.py /home/pcc/PCC/testing/master/src/ test_list_1"

The first argument is the location of a PCC source directory inside the VM image. Soon, we plan to support:
1. Local source directories. We will copy a local directory to the VM, build the scheme and test it, with an option to
delete the source from the VM afterward, so the image is largely unchanged.
2. Github repos/branches. We will use a read-only access account to pull a branch on the VM, build it and test it, with
an option to remove the branch when finished.
3. Any scheme already in Pantheon. We will use the implementation found on the vim in
/home/pcc/PCC/testing/pantheon/thir_party.

### Viewing per-RTT traces of results:
After the test runs, results will be in "results/test_1/todays_date/pcc_test_scheme_<some_number>.json".

These traces aren't perfect yet, and there may be better ways to get per-RTT or interval-based statistics from Pantheon
logs, but this is a start.

### Viewing graphs of results:
To see a graph of various performance characteristics from this run (and all runs of the same test on the same date) run:
"python3 ./graphing/pcc_grapher.py ./results/test_1/tpdays_date/ ./graphing/graphs/sample.json"

If there is a per-RTT statistic you see in the .json log files that you would like to see in the graph, you can edit
sample.json and add it to the group of variables already graphed.

