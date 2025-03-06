from datetime import datetime, timedelta
import re
from log import get_logger

class Analysis:
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)

    def cleanup_data(self):
        # Keep only the last attempt for each test
        for student, data in self.app.students_data.items():
            latest_attempts = {}
            for result in data["results"]:
                test_number = result["test_number"]
                if test_number not in latest_attempts or result["endTime"] > latest_attempts[test_number]["endTime"]:
                    latest_attempts[test_number] = result

            # Replace with filtered results
            self.app.students_data[student]["results"] = list(latest_attempts.values())

    def structure_data(self):
        thirty_days_ago = datetime.now() - timedelta(days=30)
        valid_tests = {}
        valid_results = []
        students_data = self.app.students_data

        for testId, test in self.app.tests.items():
            if datetime.fromisoformat(test["createdTime"]) > thirty_days_ago:   # Remove tests created more than 30 days ago
                try:
                    test_number = int(test["name"].split(".")[0])               # Remove tests with invalid names
                    valid_tests[testId] = test
                except:
                    pass

        for result in self.app.results:
            if datetime.fromisoformat(result["endTime"]) > thirty_days_ago:     # Remove results created more than 30 days ago
                if result["participant"] in self.app.conf.students:             # remove results with wrong participant
                    valid_results.append(result)

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
                    "quantity": 0,
                    "average_score": 0,
                    "overall_score": 0,
                    "results": []
                }

            # Add test result to the students results
            students_data[student_name]["results"].append(test_result)
            students_data[student_name]["quantity"] += 1
            students_data[student_name]["average_score"] += result["score"]

        self.app.students_data = students_data
        
        # Calculate average score and overall score for each student
        for student, data in self.app.students_data.items():
            # Average score
            data["average_score"] /= data["quantity"]
            
            # Calculate percentage of completed tests
            unique_test_ids = {result["test_number"] for result in data["results"]}
            percentage_completed = len(unique_test_ids) / len(valid_tests) * 100
            
            # Overall score (average score + percentage completed / 2)
            data["overall_score"] = (data["average_score"] + percentage_completed) / 2

        self.cleanup_data()

        # Extracting data
        students_tests = sorted(
            [(name, len(data["results"]), data["average_score"]) for name, data in self.app.students_data.items()], 
            key=lambda x: (-x[1], -x[2])  # Sort by quantity (desc), then by average_score (desc)
        )
        self.app.students_tests = [(name, quantity) for name, quantity, _ in students_tests]
        self.app.students_scores = sorted([(name, data["average_score"]) for name, data in self.app.students_data.items()], key=lambda x: x[1], reverse=True)
        self.app.students_overall = sorted([(name, data["overall_score"]) for name, data in self.app.students_data.items()], key=lambda x: x[1], reverse=True)

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

        # Extract and sort tests by numerical order
        self.app.sorted_tests = sorted(
            [data["name"] for data in valid_tests.values()], 
            key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else float('inf')
        )