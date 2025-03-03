import requests
from lib.Conf import Conf

class Gist:
    def update(content):
        conf = Conf()

        # settings
        token = conf.token
        gist_id = conf.gist_id
        filename = conf.filename
        content = "# Updated Content\nThis is micky mouse"

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
