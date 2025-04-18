import requests
import re
import time
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from log import get_logger

class Downloader:
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)

    def fix_isoformat(self, time):
        if '.' in time:
            timestamp, microseconds = time.split('.')   # Split the timestamp and microseconds
            microseconds = microseconds.ljust(6, '0')   # Pad microseconds to 6 digits
            return f"{timestamp}.{microseconds}"        # Reassemble the timestamp with fixed microseconds
        return time + ".000000"                         # Return the string unchanged if no microseconds part

    def fix_isoformat(self, time):
        if '.' in time:
            timestamp, microseconds = time.split('.')       # Split the timestamp and microseconds
            microseconds = microseconds.rstrip('Z')         # Remove Z if present
            microseconds = microseconds.ljust(6, '0')[:6]   # Pad to exactly 6 digits
            fixed_time = f"{timestamp}.{microseconds}"      # Reassemble the timestamp with fixed microseconds
        else:
            fixed_time = time + ".000000"                   # Return the string unchanged if no microseconds part
        
        if fixed_time.endswith('Z'):
            dt = datetime.fromisoformat(fixed_time.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(fixed_time)
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        utc_plus_5 = dt.astimezone(timezone(timedelta(hours=5))) # Convert to UTC+5
        
        return str(utc_plus_5.isoformat(timespec='microseconds'))

    def api_downloader(self, url):
        api_key = self.app.conf.api_key
        url = "https://api.onlinetestpad.com/" + url
        headers = {"accept": "application/json", "Access-Token": api_key}

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            self.logger.info(f'ERROR (Downloader -> api_downloader): {response.status_code} """{response.text}""" was added')
            raise HTTPException(f'Error when accessing api of: {url}')
        return response.json()

    def gather_tests(self, future_tests):
        composed_new_tests = {}
        new_tests = future_tests.result()

        for new_test in new_tests:
            new_test_id = new_test["id"]
            new_test_name = new_test["name"]

            composed_test_data = {}
            composed_test_data["name"] = new_test["name"]
            composed_test_data["createdTime"] = self.fix_isoformat(new_test["createdTime"])

            if new_test_id in self.app.tests:
                old_test_name = self.app.tests[new_test_id]["name"]
                if old_test_name != new_test_name:
                    old_test_name = new_test_name  # update test name 
                    self.new_data = True
                    self.logger.info(f'Name of test "{old_test_name}" was updated to "{new_test_name}"')
            else:
                self.app.tests[new_test_id] = composed_test_data  # add new test
                self.new_data = True
                self.logger.info(f'New test "{new_test_name}" was added')

            composed_new_tests[new_test_id] = composed_test_data

        # remove deleted tests
        for old_test in list(self.app.tests):
            if old_test not in composed_new_tests:
                self.logger.info(f'Test {old_test} "{self.app.tests[old_test]["name"]}" was deleted')
                del self.app.tests[old_test]
                self.new_data = True

    def gather_results(self, results_fetcher):
        composed_new_results = []
        for test_id, future in results_fetcher.items():
            new_results = future.result()

            for new_result in new_results:
                new_result_id = new_result["resultId"]

                composed_result_data = {
                    "testId": test_id,
                    "resultId": new_result["resultId"], 
                    "endTime": self.fix_isoformat(new_result["endTime"]),
                    "elapsedSeconds": new_result["elapsedSeconds"],
                    "url": new_result["url"]
                }

                composed_new_results.append(composed_result_data) # Add result

        return composed_new_results

    def gather_additional_results(self, additional_results_fetcher):
        composed_new_additional_results = []
        for test_id, future in additional_results_fetcher.items():
            new_detailed_result = future.result()

            composed_result_data = {}
            composed_result_data["testId"] = new_detailed_result["testId"]
            composed_result_data["resultId"] = new_detailed_result["resultId"]

            # get participant name
            participant = "Unknown"
            for question in new_detailed_result.get("questions", []):
                if "Кто вы?" in question.get("text", ""):  # Check if question contains "Кто вы?"
                    if question.get("answers") and len(question["answers"]) > 0:
                        participant = question["answers"][0]["answer"]
                        participant = re.sub(r"<.*?>", "", participant)  # Remove HTML tags
                        break
            composed_result_data["participant"] = participant

            # get participant score
            score = 0
            for result in new_detailed_result.get("results", []):
                if result.get("name") == "Процент правильных ответов (%)":
                    score = result["value"]
                    break
            composed_result_data["score"] = score

            composed_new_additional_results.append(composed_result_data) # Add result

        return composed_new_additional_results

    def get_test_id_to_number(self):
        test_id_map = {}
        for test_id, test_data in self.app.tests.items():
            number_part = test_data['name'].split('.')[0]
            test_id_map[test_id] = int(number_part) if number_part.isdigit() else None
        return test_id_map

    def gather(self):
        self.new_data = False
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.logger.info('Starting gathering sequence')

            # gather tests
            future_tests = executor.submit(self.api_downloader, 'tests')
            self.gather_tests(future_tests)
            test_id_to_number = self.get_test_id_to_number()
            test_numbers = [num for num in test_id_to_number.values() if num is not None]
            test_numbers_str = ", ".join(map(str, sorted(test_numbers)))
            self.logger.info(f'Gathered {len(self.app.tests)} tests ({test_numbers_str}). Gathering results ...')
            
            # gather results
            results_fetcher = {}
            for test in self.app.tests:
                results_fetcher[test] = executor.submit(self.api_downloader, f'tests/{test}/results')
            new_results = self.gather_results(results_fetcher)

            # gather additional results
            additional_results_fetcher = {}
            for new_result in new_results:
                additional_results_fetcher[new_result["resultId"]] = executor.submit(self.api_downloader, f'tests/{new_result["testId"]}/results/{new_result["resultId"]}')
            new_additional_results = self.gather_additional_results(additional_results_fetcher)

            # combine new_additional_results and new_results
            for new_result in new_results:
                for new_additional_result in new_additional_results:
                    if new_additional_result['testId'] == new_result['testId'] and new_additional_result['resultId'] == new_result['resultId']:
                        new_result.update(new_additional_result)
                        break

            # add new results and check for score changes
            for new_result in new_results:
                existing_result = next((result for result in self.app.results if result['resultId'] == new_result['resultId']), None)
                test_number = self.get_test_id_to_number().get(new_result['testId'], '0')

                if existing_result is None:
                    self.app.results.append(new_result)
                    self.new_data = True
                    self.logger.info(f"New result {new_result['resultId']} in test #{test_number} was added")
                else:
                    if existing_result['score'] != new_result['score']:
                        existing_result.update(new_result)
                        self.new_data = True
                        self.logger.info(f"Result {new_result['resultId']} in test #{test_number} was updated with a new score")

            # Remove deleted results
            for old_result in self.app.results[:]:  # Use a copy of the list to avoid issues while iterating and modifying
                if old_result not in new_results:
                    self.app.results.remove(old_result)
                    self.new_data = True
                    test_number = self.get_test_id_to_number().get(old_result['testId'], '0')
                    self.logger.info(f"Result {old_result['resultId']} in test #{test_number} was removed")

            self.logger.info(f'Gathered {len(self.app.results)} results')