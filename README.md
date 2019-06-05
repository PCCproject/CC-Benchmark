# PCC-Tester

A (prototype) push-button testing environment for congestion control.

## Installation

Scripts not yet available.

To run the PCC-Tester, you must:
1. Run a version of the pcc_tester VM (acct: pcc, password: pcc) either locally or remotely. It's about 8GB, so it
doesn't seem wise to put it on the git repo. Feel free to email Nathan (njay2 at illinois dot edu) to arrange a way to
get the vm image.
2. Copy "run_vm_test.py" to the machine with your pcc_tester VM on it.
3. Point "run_remote_test.py" to the location of run_vm_test.py on a remote machine (needs hostname and directory).
4. Update "run_remote_test.py" to reflect your choice of local results directory.
5. Install any missing python3 packages that we used. Until we get a script, the easiest way to find these is just to
run "run_remote_test.py" and see what it tries to import.

## Usage

### Running the tests
You can run a test of many schemes in Pantheon using:
./run_remote_test.py "scheme_1 scheme_2" test_name

For example:
./run_remote_test.py "default_tcp vivace_latency" loss_rate_sweep_small

Will run a few tests with different loss rates for both TCP Cubic and PCC-Vivace (the NSDI version).

To run a test from a github repo (currently only PCCProject/PCC-Uspace and netarch/PCC are supported), you can do the
following:

./run_remote_test.py PCC-Uspace:master loss_rate_sweep_small

This will automatically pull and build the code from PCC-Uspace's master branch before testing it.

Note: This only works if your version can be built with a Makefile in the /repo/src/ directory, and may need to be
changed if your executable or command line arguments differ from PCCProject/PCC-Uspace:master.

### Viewing per-RTT traces of results:
After the test runs, results will be in "results/test_1/todays_date/pcc_test_scheme_<some_number>.json".

These traces aren't perfect yet, and there may be better ways to get per-RTT or interval-based statistics from Pantheon
logs, but this is a start.

### Viewing graphs of results:
To see a graph of various performance characteristics from this run (and all runs of the same test on the same date) run:
"python3 ./graphing/pcc_grapher.py ./results/test_1/todays_date/ ./graphing/graphs/sample.json"

If there is a per-RTT statistic you see in the .json log files that you would like to see in the graph, you can edit
sample.json and add it to the group of variables already graphed.
