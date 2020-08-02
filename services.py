import string
import random


def generate_slug(redis_obj) :
    slug = ''.join([random.choice(string.ascii_letters) for _ in range(8)])
    if slug in list(map(lambda x : x.decode('utf8'), redis_obj.smembers('slug_set'))) :
        return generate_slug(redis_obj)
    redis_obj.sadd('slug_set', slug)
    return slug


def normalize_schedule(schedule_list) :
    return list(map(lambda x : (x['num'], x['room'], x['name'], x['slug']), schedule_list))
