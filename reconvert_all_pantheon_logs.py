#!/usr/bin/python3
from python_utils.file_locations import results_dir
from graphing.analysis.results_library import ResultsLibrary

results = ResultsLibrary(results_dir)
results.reconvert_all_pantheon_logs()
