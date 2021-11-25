import json
from pathlib import Path
import sys

import numpy as np
from tqdm import tqdm

from src.simple.statistics import Statistics

DATA_DIRECTORY = Path("..") / Path("..") / Path("data")


def get_test_occurrences(project, build_id):
    project_dir = DATA_DIRECTORY / Path(f"{project}")
    filename = project_dir / Path("testOccurrences") / Path(f"{build_id}.json")
    with open(filename, "r") as file:
        return json.load(file)


def num_flaky(test_info, failed_to_run_fraction):
    count = 0
    all_tests = 0
    for test_name, run in test_info.num_runs.items():
        all_tests += 1
        failed = test_info.num_failed.get(test_name, 0)
        if failed / run >= failed_to_run_fraction:
            count += 1
    return count / all_tests


def calc_flaky_count(test_info):
    failed_to_run_fractions = np.linspace(0, 1, 100)
    num_flakys = [num_flaky(test_info, fraction) for fraction in failed_to_run_fractions]
    return failed_to_run_fractions, num_flakys


class Pipelines:
    def __init__(self, test_info, test_filter, test_rank):
        self.test_info = test_info
        self.test_filter = test_filter
        self.test_rank = test_rank

    def __calc_metric(self, project, builds, test_metrics):
        metric_results = []
        all_tests = []
        for build_id in tqdm(builds, file=sys.stdout):
            test_occurrences = get_test_occurrences(project, build_id)
            all_tests.append(test_occurrences)
            if not test_occurrences:
                continue

            # tests_filtered = test_filter.filter(test_occurrences, test_info)
            tests_ranked = self.test_rank.rank(test_occurrences, self.test_info)
            metric_results.append([test_metric.measure(tests_ranked, test_occurrences) for test_metric in test_metrics])

            self.test_info.update(test_occurrences)
        flaky_test_stats = calc_flaky_count(self.test_info)
        metric_names = [metric.name for metric in test_metrics]
        metrics = zip(metric_names, np.transpose(metric_results))
        return Statistics(project, metrics, flaky_test_stats)

    def run_all_with_metrics(self, project, test_metrics):
        project_dir = DATA_DIRECTORY / Path(f"{project}")
        with open(project_dir / Path("builds_info.json"), "r") as file:
            builds_info = json.load(file)
            builds = builds_info[::-1]  # chronological order
            print("# builds =", len(builds))
            return self.__calc_metric(project, builds, test_metrics)