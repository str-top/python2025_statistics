from Analysis import Analysis
from Conf import Conf
from Conversion import Conversion
from Downloader import Downloader
from Gist import Gist
import time

class App:
    def __init__(self):
        self.tests = {}         # tests data
        self.results = []       # results data
        self.students_data = {} # analyzed data
        self.content = ""       # resulting formatted data

        self.gist = Gist(self)
        self.downloader = Downloader(self)
        self.conf = Conf(self)
        self.analysis = Analysis(self)
        self.conversion = Conversion(self)

    def run(self):
        while True:
            anything_new = self.downloader.gather_data() # fetch data from onlinetestpad.com
            if not anything_new:
                time.sleep(30)
                continue
            
            self.analysis.analyse()  # prepare data

            for student in self.students_data:
                print(student, self.students_data[student])

            self.conversion.convert() # convert data to markdown

            self.gist.update() # upload data to gist
            break

app = App()
app.run()


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