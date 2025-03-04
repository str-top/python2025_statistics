from Gist import Gist
from Downloader import Downloader
from Conf import Conf
import time

class App:
	def __init__(self):
		self.tests = {}  # TEST RESULTS DATA
		self.content = ""

		self.gist = Gist(self)
		self.downloader = Downloader(self)
		self.conf = Conf(self)


	def run(self):
		while True:
			# fetch data from onlinetestpad.com
			anything_new = self.downloader.gather_data()
			if not anything_new:
				time.sleep(60)
				continue

			# 2) analyze_data
			# 3) convert to md

			# upload to gist
			# self.gist.update(self.content)

			time.sleep(6)
			break

app = App()
app.run()


# DATA STRUCTURE:
# {"pvomsfav2jpts":
#  {"name": "Test 1. Modifiers",
#   "createdTime": "2025-02-27T15:39:28.039268",
#   "results":
#    [
#     {
#      "resultId": "res_102"
#      "testId": "test_1"
#      "endTime": "2024-03-04T11:00:00Z"
#      "elapsedSeconds": 2200
#      "url": "http://example.com/result/102"
#      "participant": "Bob"
#      "score": 90
#     },
#     ...
#    ]
#  },
#  ...
# }