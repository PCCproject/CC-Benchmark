#!/usr/bin/python3

import average_metric
import average_jain_idx
import scp_to_cpanel

def main():
    test_data_dir = '/Users/jaewooklee/PCC-Tester/pcc-web/test_data/'
    multiflow_dir = set()
    average_metric.merge_metric_for_all_test(test_data_dir, multiflow_dir)
    average_jain_idx.merge_all_jain_idx_with_multiflow(test_data_dir, multiflow_dir)
    scp_to_cpanel.scp_to_cpanel()

if __name__ == '__main__':
    main()
