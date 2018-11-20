#!/usr/bin/python3
import os

from python_utils import github_utils

here = os.path.dirname(__file__)
github_utils.pull_from_repo("PCC-Tester", here)
