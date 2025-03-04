import configparser
import os

class Conf:

	def __init__(self, app):
		self.app = app
		config = configparser.ConfigParser()
		config.read("config.ini")

		self.api_key = config['onlinetestpad']['api_key']

		self.token = config['github']['token']
		self.gist_id = config['github']['gist_id']
		self.filename = config['github']['filename']