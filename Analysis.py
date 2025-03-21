from datetime import datetime, timedelta
import re
from log import get_logger

class Analysis:
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)

    def cleanup_tests(self):
        self.valid_tests = {}
        for testId, test in self.app.tests.items():
            if datetime.fromisoformat(test["createdTime"]) > self.days_of_results:   # Remove tests created more than 30 days ago
                try:
                    test_number = int(test["name"].split(".")[0])               # Remove tests with invalid names
                    self.valid_tests[testId] = test
                except:
                    pass
        return self.valid_tests

    def cleanup_results(self):
        valid_results = []
        for result in self.app.results:
            if datetime.fromisoformat(result["endTime"]) > self.days_of_results:     # Remove results created more than 30 days ago
                if result["participant"] in self.app.conf.students:             # remove results with wrong participant
                    valid_results.append(result)
        return valid_results

    def construct_students_data(self):
        students_data = self.app.students_data
        valid_tests = self.cleanup_tests()
        valid_results = self.cleanup_results()
        self.logger.info(f'Constructing students data. Confirmed valid_tests: {len(valid_tests)}, valid_results: {len(valid_results)}')

        # Process the results data
        for result in valid_results:
            student_name = result["participant"]
            for test in valid_tests:
                if test == result["testId"]:
                    test_number = int(valid_tests[test]["name"].split(".")[0])
            test_result = {
                "test_number": test_number,
                "score": result["score"],
                "endTime": result["endTime"],
                "url": result["url"]
            }

            if student_name not in students_data:
                students_data[student_name] = {
                    "results": []  # Only store results here; quantity and scores will be calculated later
                }

            # Add test result to the student's results
            students_data[student_name]["results"].append(test_result)

        self.logger.debug(f'Constructed students data. Data size: {len(self.app.students_data)}')

    def remove_duplicate_attempts(self):
        # Keep only the last attempt for each test
        for student, data in self.app.students_data.items():
            latest_attempts = {}
            for result in data["results"]:
                test_number = result["test_number"]
                if test_number not in latest_attempts or result["endTime"] > latest_attempts[test_number]["endTime"]:
                    latest_attempts[test_number] = result

            # Replace with filtered results
            self.app.students_data[student]["results"] = list(latest_attempts.values())

    def construct_scores(self):
        # Calculate average score and overall score for each student
        for student, data in self.app.students_data.items():
            # Initialize quantity and average_score
            data["quantity"] = len(data["results"])  # Number of results (tests taken)
            data["average_score"] = 0  # Initialize average score

            # Calculate total score
            total_score = 0
            for result in data["results"]:
                total_score += result["score"]

            # Calculate average score
            if data["quantity"] > 0:  # Avoid division by zero
                data["average_score"] = total_score / data["quantity"]
            else:
                data["average_score"] = 0  # Default to 0 if no results are available

            # Calculate percentage of completed tests
            unique_test_ids = {result["test_number"] for result in data["results"]}
            percentage_completed = len(unique_test_ids) / len(self.valid_tests) * 100

            # Calculate overall score (average score + percentage completed / 2)
            data["overall_score"] = (data["average_score"] + percentage_completed) / 2

    def construct_results_list_for_each_student(self):
        # list of students test results
        for name, data in self.app.students_data.items():
            results = [
                {
                    "test_number": result["test_number"],
                    "url": result["url"],
                    "score": result["score"],
                    "short_date": datetime.strptime(result["endTime"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d.%m")
                }
                for result in data["results"]
            ]
            self.app.students_results.append((name, results))

    def construct_last_tests(self):
        # Extract and sort tests by numerical order
        self.app.sorted_tests = sorted(
            [data["name"] for data in self.valid_tests.values()], 
            key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else float('inf')
        )

    def construct_last_15_results(self):
        # Collect all test results from all students
        all_results = [
            (datetime.fromisoformat(res["endTime"]), res["test_number"], student)
            for student, data in self.app.students_data.items()
            for res in data["results"]
        ]

        # Sort by endTime in descending order (latest first)
        all_results.sort(reverse=True, key=lambda x: x[0])

        # Get the last 15 results
        self.app.last_15_results = all_results[:15]

    def construct_overall_scores_rating(self):
        self.app.students_overall = sorted([(name, data["overall_score"]) for name, data in self.app.students_data.items()], key=lambda x: x[1], reverse=True)

    def construct_average_scores_rating(self):
        self.app.students_scores = sorted([(name, data["average_score"]) for name, data in self.app.students_data.items()], key=lambda x: x[1], reverse=True)

    def construct_finished_tests_rating(self):
        students_tests = sorted(
            [(name, len(data["results"]), data["average_score"]) for name, data in self.app.students_data.items()], 
            key=lambda x: (-x[1], -x[2])  # Sort by quantity (desc), then by average_score (desc)
        )
        self.app.students_tests = [(name, quantity) for name, quantity, _ in students_tests]

    def construct(self):
        self.days_of_results = datetime.now() - timedelta(days=self.app.conf.days_of_results)
        self.construct_students_data()
        self.remove_duplicate_attempts()
        num_students = len(self.app.students_data)
        total_results = sum(len(student["results"]) for student in self.app.students_data.values())
        self.logger.info(f'Data structure with {num_students} students and {total_results} results has been constructed.')
        
        self.construct_scores()
        self.construct_overall_scores_rating()
        self.construct_average_scores_rating()
        self.construct_finished_tests_rating()

        self.construct_last_tests()
        self.construct_results_list_for_each_student()
        self.construct_last_15_results()