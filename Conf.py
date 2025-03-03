import configparser
import os

class Conf:

	def __init__(self):		
		config = configparser.ConfigParser()
		config.read("config.ini")

    self.token = config['conf']['token']
    self.gist_id = config['conf']['gist_id']
    self.filename = config['conf']['filename']
