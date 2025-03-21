from Analysis import Analysis
from Conf import Conf
from Conversion import Conversion
from Downloader import Downloader
from Gist import Gist
import time
from datetime import datetime
from log import get_logger
import os

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
            self.analysis.construct()  # prepare data
            
            try:
                self.conversion.convert('mentor') # convert data to markdown
                self.gist.update('mentor')        # upload data to gist
                
                self.conversion.convert('student')
                self.gist.update('student')
            except Exception as e:
                self.logger.error(f'ERROR: {e}')
                self.logger.error(f'ERROR. Sleeping for {self.time_between_queries} seconds')
                time.sleep(self.time_between_queries)
                continue

            # trim log file
            log_file = "python2025_statistics.log"
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(BASE_DIR, log_file)
            max_size = 10 * 1024 * 1024  # in MB
            if os.path.exists(full_path) and os.path.getsize(full_path) > max_size:
                with open(full_path, "rb") as f:
                    f.seek(-max_size // 2, os.SEEK_END)  # Move to last half
                    f.readline()  # Ensure we start at the next full line
                    trimmed_data = f.read()  # Read the remaining part of the file
                with open(full_path, "wb") as f:  # Overwrite file with trimmed content
                    f.write(trimmed_data)
                self.logger.info(f'Truncated log file to {os.path.getsize(full_path) / 1024 / 1024:.2f} MB')

            self.logger.info(f'Sleeping after successful program iteration for {self.time_between_queries} seconds')
            time.sleep(self.time_between_queries)

app = App()
app.run()

# TODO:
# - fix wrong result date in log