from Analysis import Analysis
from Conf import Conf
from Conversion import Conversion
from Downloader import Downloader
from Gist import Gist
import time
from datetime import datetime
from log import get_logger

class App:
    def __init__(self):
        self.logger = get_logger(__name__)

        # raw data
        self.tests = {}             # tests data
        self.results = []           # results data
        self.time_between_queries = 10

        self.gist = Gist(self)
        self.downloader = Downloader(self)
        self.conf = Conf(self)
        self.analysis = Analysis(self)
        self.conversion = Conversion(self)

    def run(self):
        self.logger.info('Starting app')
        while True:
            # analyzed data
            self.students_data = {}     # analyzed data

            # data prepared for displaying
            self.students_results = []  # list of all results for each student
            self.students_tests = []    # tests completed rating
            self.students_scores = []   # average score rating
            self.students_overall = []  # overall score rating
            self.sorted_tests = []      # list of tests for last 30 days
            self.last_15_results = []

            self.content = ""           # resulting formatted data

            try:
                self.downloader.gather() # fetch data from onlinetestpad.com
            except Exception as e:
                self.logger.error(f'ERROR: {e}')
                self.logger.error(f'ERROR. Sleeping for {self.time_between_queries} seconds')
                time.sleep(self.time_between_queries)
                continue

            if not self.downloader.new_data:
                self.logger.info(f'Nothing new, sleeping for {self.time_between_queries} seconds')
                time.sleep(self.time_between_queries)
                continue
            print('before analysis')
            self.analysis.construct()  # prepare data
            
            self.conversion.convert('mentor') # convert data to markdown
            self.gist.update('mentor')        # upload data to gist
            
            self.conversion.convert('student')
            self.gist.update('student')

            self.logger.info(f'Sleeping after successful program iteration for {self.time_between_queries} seconds')
            time.sleep(self.time_between_queries)

app = App()
app.run()

# TODO:
# + run 24/7 in vps
# - refactor code
# + view last 15 results
# - auto pull latest version from github
# + display latest update time

# TESTS DATA STRUCTURE:
# {"pvomsfav2jpts":
#  {"name": "Test 1. Modifiers",
#   "createdTime": "2025-02-27T15:39:28.039268",
#  },
#  ...
# }


# RESULTS DATA STRUCTURE:
# [
# {
#  "resultId": "res_102"
#  "testId": "test_1"
#  "endTime": "2024-03-04T11:00:00Z"
#  "elapsedSeconds": 2200
#  "url": "http://example.com/result/102"
#  "participant": "Bob"
#  "score": 90
# },
# ...
# ]