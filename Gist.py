import requests

class Gist:
    def __init__(self, app):
        self.app = app
        
    def update(content):
        token = self.app.conf.token
        gist_id = self.app.conf.gist_id
        filename = self.app.conf.filename

        # conversions
        url = "https://api.github.com/gists/" + gist_id
        data = {
            "files": {
                filename: {
                    "content": content
                }
            }
        }
        headers = {'Authorization': f'token {token}'}

        # request
        a = requests.patch(url, json=data, headers=headers)
        print(a)
