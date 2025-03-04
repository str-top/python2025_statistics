from datetime import datetime, timedelta

class Analysis:
    def __init__(self, app):
        self.app = app
        
    def analyse(self):
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
        
        # Calculate average score and overall score for each student
        for student, data in students_data.items():
            # Average score
            data["average_score"] /= data["quantity"]
            
            # Calculate percentage of completed tests
            unique_test_ids = {result["test_number"] for result in data["results"]}
            percentage_completed = len(unique_test_ids) / len(valid_tests) * 100
            
            # Overall score (average score + percentage completed / 2)
            data["overall_score"] = (data["average_score"] + percentage_completed) / 2