import requests
import os
items = requests.get(f"https://api.telegram.org/bot{os.getenv('TOKEN')}/getUpdates").json()['result']
if items:
    last_update = items[-1]
    last_update_id = last_update['update_id']
    requests.get(f"https://api.telegram.org/bot{os.getenv('TOKEN')}/getUpdates", params={
        'offset': last_update_id + 1
    })
