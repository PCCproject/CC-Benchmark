import os

python_utils_dir = os.path.dirname(os.path.abspath(__file__))
testing_dir = os.path.join(python_utils_dir, "..")
topos_dir = os.path.join(testing_dir, "topos")
tests_dir = os.path.join(testing_dir, "tests")
results_dir = os.path.join(testing_dir, "results")
pantheon_dir = os.path.join(testing_dir, "pantheon")
graphing_dir = os.path.join(testing_dir, "graphing")

vm_status_dir = "/home/pcc/vm_status/"
local_test_running_dir = vm_status_dir + "test_running"
remote_test_running_dir = vm_status_dir + "remote_test_running"
free_vm_script = vm_status_dir + "free.sh"
occupy_vm_script = vm_status_dir + "occupy_vm.sh"
