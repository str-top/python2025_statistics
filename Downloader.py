import requests
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class Downloader:
    def __init__(self, app):
        self.app = app
        self.tests = app.tests
        self.results = app.results

    # Function to fix the ISO 8601 datetime format
    def fix_isoformat(self, time):
        if '.' in time:
            timestamp, microseconds = time.split('.')   # Split the timestamp and microseconds
            microseconds = microseconds.ljust(6, '0')               # Pad microseconds to 6 digits
            return f"{timestamp}.{microseconds}"                    # Reassemble the timestamp with fixed microseconds
        return time + ".000000"                         # Return the string unchanged if no microseconds part

    def downloader(self, url):
        api_key = self.app.conf.api_key
        url = "https://api.onlinetestpad.com/" + url
        headers = {"accept": "application/json", "Access-Token": api_key}

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            return []

        return response.json()

    def gather_data(self):
        new_data = False
        with ThreadPoolExecutor() as executor:
            results = {}
            additional_results = {}

            future_tests = executor.submit(self.downloader, 'tests')
            tests = future_tests.result()

            # TODO: check funtionality
            # check if tests have been deleted
            for saved_test in self.tests:
                if saved_test not in tests:
                    new_data = True

            # Process each test
            for test in tests:
                test_id = test["id"]
                test_name = test["name"]

                new_test = {}
                new_test["name"] = test["name"]
                new_test["createdTime"] = self.fix_isoformat(test["createdTime"])

                if test_id in self.tests:
                    if self.tests[test_id]["name"] != test_name:
                        self.tests[test_id]["name"] = test_name  # update test name
                        new_data = True
                else:
                    self.tests[test_id] = new_test  # add test
                    new_data = True
                results[test_id] = executor.submit(self.downloader, f'tests/{test_id}/results')
            # return True
            # Process the results
            for test_id, future in results.items():
                results = future.result()

                # Process results for each test
                for result in results:
                    result_id = result["resultId"]

                    result_data = {
                        "testId": test_id,
                        "resultId": result["resultId"], 
                        "endTime": self.fix_isoformat(result["endTime"]),
                        "elapsedSeconds": result["elapsedSeconds"],
                        "url": result["url"]
                    }

                    # Add result
                    if result_data not in self.results:
                        self.results.append(result_data)
                        new_data = True

                    additional_results[result_id] = executor.submit(self.downloader, f'tests/{test_id}/results/{result_id}')


            # process additional results
            for test_id, future in additional_results.items():
                detailed_result = future.result()

                if detailed_result:
                    result_data = {}
                    participant = "Unknown"
                    for question in detailed_result.get("questions", []):
                        if question.get("number") == 1:
                            participant = question["answers"][0]["answer"]
                            participant = re.sub(r"<.*?>", "", participant)  # Remove HTML tags
                            break

                    score = 0
                    for result in detailed_result.get("results", []):
                        if result.get("name") == "Процент правильных ответов (%)":
                            score = result["value"]
                            break
                    result_data["participant"] = participant
                    result_data["score"] = score

                    test_id = detailed_result["testId"]
                    result_id = detailed_result["resultId"]

                    # append additional values to the correct result in self.results
                    for result in self.results:
                        if result['testId'] == test_id and result['resultId'] == result_id:
                            result.update(result_data)
                            break
            return new_data