import os
import redisdl
import yadisk as ya
from time import gmtime, strftime
OAUTH_KEY = os.getenv('OAUTH_TOKEN')
yadisk = ya.YaDisk(token=os.getenv('OAUTH_TOKEN'))
f = open('temp.json', 'w', encoding='utf8')
json_string = redisdl.dump(f)
_time = strftime('%Y_%m_%d_%H', gmtime())
year, month, day, hour = _time.split('_')
try:
    yadisk.mkdir(f'/{year}')
except ya.exceptions.DirectoryExistsError:
    pass
try:
    yadisk.mkdir(f'/{year}/{month}')
except ya.exceptions.DirectoryExistsError:
    pass
try:
    yadisk.mkdir(f'/{year}/{month}/{day}')
except ya.exceptions.DirectoryExistsError:
    pass
f.close()
yadisk.upload('temp.json', f'/{year}/{month}/{day}/{hour}.json', overwrite=True)
f = open('temp.json', 'w')
f.close()
