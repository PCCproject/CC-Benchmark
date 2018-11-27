#!/usr/bin/python3
from python_utils.file_locations import results_dir
from graphing.analysis.results_library import ResultsLibrary

results = ResultsLibrary(results_dir)
results.delete_no_metadata_tests()
