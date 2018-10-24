#!/usr/bin/env python

import sys
from subprocess import Popen, call, check_call
from src_helpers import (parse_arguments, wait_and_kill_iperf,
                         check_default_qdisc)
from helpers.helpers import get_kernel_attr


def setup_bbr():

    # add bbr to kernel-allowed congestion control list
    sh_cmd = 'sysctl net.ipv4.tcp_allowed_congestion_control'
    allowed_cc = get_kernel_attr(sh_cmd, debug=False)

    if 'pcc' not in allowed_cc:
        allowed_cc.append('pcc')

        sh_cmd = 'sudo sysctl -w net.ipv4.tcp_allowed_congestion_control="%s"'
        check_call(sh_cmd % ' '.join(allowed_cc), shell=True)

    check_default_qdisc('pcc')


def main():
    args = parse_arguments('receiver_first')

    if args.option == 'deps':
        print 'iperf'

    if args.option == 'run_first':
        print 'receiver'

    if args.option == 'setup_after_reboot':
        setup_bbr()

    if args.option == 'receiver':
        cmd = ['iperf', '-Z', 'pcc', '-s', '-p', args.port]
        wait_and_kill_iperf(Popen(cmd))

    if args.option == 'sender':
        cmd = ['iperf', '-Z', 'pcc', '-c', args.ip, '-p', args.port,
               '-t', '300']
        wait_and_kill_iperf(Popen(cmd))


if __name__ == '__main__':
    main()
