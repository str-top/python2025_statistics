import requests
from log import get_logger

class Gist:
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        
    def update(self, role):
        if role == 'mentor':
            self.request(self.app.conf.gist_id_admin)
        else:
            self.request(self.app.conf.gist_id)

    def request(self, gist_id):
        token = self.app.conf.token
        filename = self.app.conf.filename

        # conversions
        url = "https://api.github.com/gists/" + gist_id
        data = {
            "files": {
                filename: {
                    "content": self.app.content
                }
            }
        }
        headers = {'Authorization': f'token {token}'}

        # request
        a = requests.patch(url, json=data, headers=headers)
    
        if a.status_code in [200, 201, 204]:
            self.logger.info(f'Successfully uploaded file to gist')
        else:
            self.logger.error(f'Upload to gist failed! Status code: {a.status_code}, Response: {a.text}"')