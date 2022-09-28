#!/usr/bin/env python

'''Example file to add a new congestion control scheme.

Please use Python 2.7 and conform to PEP8. Also use snake_case as file name and
make this file executable.
'''

import os
from os import path
from subprocess import check_call
from src_helpers import parse_arguments, check_default_qdisc
import project_root  # 'project_root.DIR' is the root directory of Pantheon
import random

def main():
    # use 'parse_arguments()' to ensure a common test interface
    args = parse_arguments('receiver_first')  # or 'sender_first'

    if args.option == 'run_first':
        print 'receiver'

    if args.option == 'setup':
        pass # Assume the other scripts have done all the setup.

    if args.option == 'setup_after_reboot':
        pass # Assume the other scripts have done all the setup.

    if args.option == 'receiver':
        os.environ['LD_LIBRARY_PATH'] = 'sprout copa/core'
        cmd = ('sprout copa/app/pccserver recv').split(' ') + [args.port]
        check_call(cmd)

    if args.option == 'sender':
        os.environ['LD_LIBRARY_PATH'] = 'sprout copa/core'
        cmd = ('sprout copa/app/pccclient send').split(' ') + [args.ip, args.port] # Replaced with extra args if needed
        check_call(cmd)


if __name__ == '__main__':
    main()
