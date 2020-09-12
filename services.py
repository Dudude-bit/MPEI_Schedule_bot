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


def create_main_keyboard():
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='weekdays:current')
    btn2 = telebot.types.InlineKeyboardButton(text='Поменять группу', callback_data='change_group')
    btn3 = telebot.types.InlineKeyboardButton(text='О боте', callback_data='about')
    kb.row(btn1)
    kb.row(btn2, btn3)
    return kb


def decorator(func):
    def wrapper(message):
        print(datetime.datetime.now())
        return func(message)
    return wrapper
