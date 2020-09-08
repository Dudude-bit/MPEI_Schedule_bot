import string
import random

import telebot
import datetime


def generate_slug(redis_obj):
    slug = ''.join([random.choice(string.ascii_letters) for _ in range(8)])
    if slug in list(map(lambda x: x.decode('utf8'), redis_obj.smembers('slug_set'))):
        return generate_slug(redis_obj)
    redis_obj.sadd('slug_set', slug)
    return slug


def normalize_schedule(schedule_list):
    return list(map(lambda x: (x['num'], x['room'], x['name'], x['slug']), schedule_list))


def create_main_keyboard():
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='weekdays:current')
    btn2 = telebot.types.InlineKeyboardButton(text='Настройки', callback_data='settings')
    kb.row(btn1)
    kb.row(btn2)
    return kb


def decorator(func):
    def wrapper(message):
        print(datetime.datetime.now())
        return func(message)
    return wrapper
