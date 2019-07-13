#!/usr/bin/python3

import average_metric
import average_jain_idx
import rsync_with_cpanel
import get_overall_score

def main():
    test_data_dir = '/srv/shared/PCC/testing/pcc-web/test_data/'
    multiflow_dir = set()
    average_metric.merge_metric_for_all_test(test_data_dir, multiflow_dir)
    average_jain_idx.merge_all_jain_idx_with_multiflow(test_data_dir, multiflow_dir)
    get_overall_score.get_overall_score(test_data_dir)
    rsync_with_cpanel.rsync_with_cpanel()

if __name__ == '__main__':
    main()
