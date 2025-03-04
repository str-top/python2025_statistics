import requests
import re

class Downloader:
    def __init__(self, app):
        self.app = app
        self.tests = app.tests

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

        # process tests
        for test in self.downloader('tests'):
            test_id = test["id"]
            test_name = test["name"]

            if test_id in self.tests:
                if self.tests[test_id]["name"] != test_name:
                    self.tests[test_id]["name"] = test_name   # update test name
                    new_data = True
                    print(f"Updated name for test ID {test_id}: {test_name}")
            else:
                self.tests[test_id] = test # add test
                self.tests[test_id]["results"] = [] # initialize results
                new_data = True
                print(f"Added new test: {self.tests[test_id]}")

            # process results
            for result in self.downloader(f'tests/{test_id}/results'):
                result_id = result["resultId"]

                result_data = {
                    "resultId": result_id,
                    "endTime": result["endTime"],
                    "elapsedSeconds": result["elapsedSeconds"],
                    "url": result["url"]
                }

                # process results (additional)
                detailed_result = self.downloader(f'tests/{test_id}/results/{result_id}')   
                if detailed_result:
                    participant = "Unknown"
                    for question in detailed_result.get("questions", []):
                        if question.get("number") == 1:
                            participant = question["answers"][0]["answer"]
                            participant = re.sub(r"<.*?>", "", participant)
                            break

                    score = 0
                    for result in detailed_result.get("results", []):
                        if result.get("name") == "Процент правильных ответов (%)":
                            score = result["value"]
                            break

                    result_data["participant"] = participant
                    result_data["score"] = score

                if result_data not in self.tests[test_id]["results"]:
                    self.tests[test_id]["results"].append(result_data)
                    print(f"Added new result: {result_data}")
                    new_data = True

        return new_data