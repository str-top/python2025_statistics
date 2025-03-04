
class Conversion:
	def __init__(self, app):
		self.app = app
		
	def convert(self):
		for test in self.app.tests:
			self.app.content += '\n' + test + ": " + str(self.app.tests[test])
		for student in self.app.students_data:
			self.app.content += '\n' + student + ' ' + str(self.app.students_data[student])
