import os

python_utils_dir = os.path.dirname(os.path.abspath(__file__))
testing_dir = os.path.join(python_utils_dir, "..")
topos_dir = os.path.join(testing_dir, "topos")
tests_dir = os.path.join(testing_dir, "tests")
results_dir = os.path.join(testing_dir, "results")
pantheon_dir = os.path.join(testing_dir, "pantheon")
graphing_dir = os.path.join(testing_dir, "graphing")

local_test_running_dir = "/tmp/test_running"
remote_test_running_dir = "/tmp/remote_test_running"
