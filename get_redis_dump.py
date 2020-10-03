import json
import yadisk as ya
import redis
yadisk = ya.YaDisk(token='AgAAAAA50RCLAAadkzzPvN2mYkRkiYmUUQeEssY')

r = redis.Redis(host='redis')
path = list(yadisk.get_last_uploaded())[0].path

yadisk.download(path, 'temp.json')

file = open('temp.json')
str_json = file.read()
file.close()
file = open('temp.json', 'w')
file.close()
json = json.loads(str_json)
for key in json:
    if json[key]['type'] == 'string':
        r.set(key, json[key]['value'])
    elif json[key]['type'] == 'set':
        for val in json[key]['value']:
            r.sadd(key, val)
    elif json[key]['type'] == 'list':
        for val in json[key]['value']:
            r.rpush(key, val)

