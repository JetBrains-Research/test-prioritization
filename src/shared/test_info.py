from src.shared.base_models import TestOccurrencesInfo


class TestInfo(TestOccurrencesInfo):
    def __init__(self, gamma):
        self.gamma = gamma
        self.num_runs = {}
        self.num_failed = {}
        self.num_success = {}
        self.file_changed_test_failed = {}
        self.changed_files = None

    def update(self, test_occurrences):
        for test in test_occurrences:
            test_name, status = test["name"], test["status"]
            if test.get("ignored") or status not in ["SUCCESS", "FAILURE"]:
                continue
            self.num_runs[test_name] = self.num_runs.get(test_name, 0) * self.gamma + 1
            self.num_success[test_name] = self.num_success.get(test_name, 0) * self.gamma
            self.num_failed[test_name] = self.num_failed.get(test_name, 0) * self.gamma

            if test["status"] == "SUCCESS":
                self.num_success[test_name] += 1
            elif test["status"] == "FAILURE":
                self.num_failed[test_name] += 1
                for filename in self.changed_files:
                    key = (filename, test_name)
                    self.file_changed_test_failed[key] = self.file_changed_test_failed.get(key, 0) + 1
