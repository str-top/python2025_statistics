import configparser
import os

class Conf:

    def __init__(self, app):
        self.app = app
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")
        config = configparser.ConfigParser()
        config.read("config.ini")

        self.api_key = config['onlinetestpad']['api_key']
        self.students = config["onlinetestpad"]["students"].split(", ")

        self.token = config['github']['token']
        self.gist_id = config['github']['gist_id']
        self.gist_id_admin = config['github']['gist_id_admin']
        self.filename = config['github']['filename']