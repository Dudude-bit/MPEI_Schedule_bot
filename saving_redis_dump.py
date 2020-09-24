import os
import redisdl
import tempfile
import yadisk as ya
from time import gmtime, strftime
OAUTH_KEY = 'AgAAAAA50RCLAAadkzzPvN2mYkRkiYmUUQeEssY'
yadisk = ya.YaDisk(token=OAUTH_KEY)

with tempfile.NamedTemporaryFile() as f:
    redisdl.dump(f)
    time = strftime('%Y_%m_%d_%H', gmtime())
    year, month, day, hour = time.split('_')
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
    yadisk.upload(f.name, f'/{year}/{month}/{day}/{hour}.json', overwrite=True)

