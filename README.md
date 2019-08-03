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

## Creating new tests

### Naming convention
<<<<<<< HEAD
1. Make sure not to include - or . in the test directory.
2. Create a directory under _tests_, e.g. _tests/**bandwidth_sweep**_
3. Create test file(s) under directory created from 2. Include the parameters in the name of the created files, e.g. _tests/bandwidth_sweep/**1mpbs.json**_. 
4. The 'name' field of the test inside json file should be test-directory.detail, e.g. _bandwidth_sweep.1mbps_
5. The filename of the test must match the detail part of the name, e.g. _bandwidth_sweep.1mbps_ should be named _1mbps.json_.
6. For tests with varying bandwidth, latency, or loss for each flow, detailed part of the test name should be separated by _to_ keyword, e.g. 1mbps_to_0.1loss_to_30ms means the bandwidth of the first flow is 1mbps, the loss rate of the second flow is 0.1, and the latency of the third flow is 30ms. Note of the keywords **_mbps, loss, and ms._**

### Creating html for newly created tests
1. Create a directory under pcc-web/test_data named _test-directory_test_. e.g. pcc-web/test_data/**bandwidth_sweep_test**.
2. Create an index.html under the directory created from 1. Refer to [pcc-web/test_data/singleflow_index.html](pcc-web/test_data/singleflow_index.html) or [pcc-web/test_data/multiflow_index.html](pcc-web/test_data/multiflow_index.html) depending on the test and fill out index.html.
3. Refer to pcc-web/test_data/detailed_flow.html to create htmls for detailed traces **per scheme**. The currently supported schemes are [tcp-cubic, vivace latency, copa, bbr, ledbat, pcc, sprout, taova, vegas]. 
4. (Optional) Include alias file under directory created from 1, e.g. pcc-web/test_data/rtt_fairness3/alias, only if you would like the test to be called differently or would like to provide more information. Note that the alias file should include exactly what you want the test to be called in one line and nothing else. For reference, take a look at [this](pcc-web/test_data/rtt_fairness3/alias).
=======
1. Make sure not to include - or . in the test name.
2. The name of the test should be testname.detail, e.g. _bandwidth_sweep.1mbps_
3. The filename of the test must match the detail part of the name, e.g. _bandwidth_sweep.1mbps_ should be named _1mbps.json_.
4. For tests with varying bandwidth, latency, or loss for each flow, detailed part of the test name should be separated by _to_ keyword, e.g. 1mbps_to_0.1loss_to_30ms means the bandwidth of the first flow is 1mbps, the loss rate of the second flow is 0.1, and the latency of the third flow is 30ms. Note of the keywords **_mbps, loss, and ms._**

### Creating html for newly created tests
1. Create a directory under pcc-web/test_data named _testname_test_. e.g. pcc-web/test_data/bandwidth_sweep_test.
2. Create an index.html under the directory created from 1.
3. Refer to pcc-web/test_data/singleflow_index.html or pcc-web/test_data/multiflow_index.html depending on the test and fill out index.html created from 2.
4. Refer to pcc-web/test_data/detailed_flow.html to create htmls for detailed traces **per scheme**. The currently supported schemes are [tcp-cubic, vivace latency, copa, bbr, ledbat, pcc, sprout, taova, vegas]. 
>>>>>>> master
5. Run the test with --web-result!

## Web Results

### Running the tests with --web-result
<<<<<<< HEAD
`./run_remote_test.py "scheme_1 scheme_2" test_name #num_replicas --web-result`<br>
will automatically push the test results to the website.

## Optional Flags
**--shutdown** will shutdown the vms after running all the tests.<br>
`./run_remote_test.py "scheme_1 scheme_2" test_name #num_replicas --shutdown`<br>
**--web-result** will automatically update pcctesting.web.illinois.edu with new results.<br>
`./run_remote_test.py "scheme_1 scheme_2" test_name #num_replicas --web-result`
=======
./run_remote_tesy.py "scheme_1 scheme_2" test_name #num_replicas --web-result
will automatically push the test results to the website.

>>>>>>> master
