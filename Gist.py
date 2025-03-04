import requests

class Gist:
    def __init__(self, app):
        self.app = app
        
    def update(self):
        self.request(self.app.conf.gist_id)
        self.request(self.app.conf.gist_id_admin)

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
        print(a)
