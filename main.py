import datetime
import logging
import os
import random
import time

import redis
import telebot
from telebot.apihelper import ApiException

import db
import exceptions
import parsing

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(token=TOKEN)

redis = redis.Redis()

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    filename='log.log')

START, SETTINGS_CHANGE_GROUP = range(2)


@bot.message_handler(commands=['start'])
def handling_start(message):
    redis.set(f'step:{message.from_user.id}', START)
    redis.sadd('unique_users', message.chat.id)
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='schedule')
    btn2 = telebot.types.InlineKeyboardButton(text='Настройки', callback_data='settings')
    kb.row(btn1)
    kb.row(btn2)
    user_group = redis.get(f'user_group:{message.from_user.id}')
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    if user_group:
        user_group = user_group.decode('utf8')
        current_week = redis.get('current_week')
        continue_text = f'студент {user_group} {emoji}. Сегодня идет {current_week} неделя'
        bot.send_message(message.chat.id, text=f'Привет, {continue_text}', reply_markup=kb)
    else:
        redis.set(f'step:{message.from_user.id}', value=SETTINGS_CHANGE_GROUP)
        bot.send_message(message.chat.id, 'Привет, Введите, пожалуйста, номер группы')


@bot.callback_query_handler(func=lambda m: m.data == 'back_to_main')
def handling_back_to_main(callback_query):
    redis.set(f'step:{callback_query.from_user.id}', START)
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='schedule')
    btn2 = telebot.types.InlineKeyboardButton(text='Настройки', callback_data='settings')
    kb.row(btn1)
    kb.row(btn2)
    user_group = redis.get(f'user_group:{callback_query.from_user.id}')
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    if user_group:
        user_group = user_group.decode('utf8')
        continue_text = f'студент {user_group} {emoji}'
    else:
        continue_text = f'МЭИшник {emoji}'
    bot.edit_message_text(text=f'Привет, {continue_text}', chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m: m.data == 'schedule')
def handling_schedule(callback_query):
    if not (redis.get(f'user_group:{callback_query.from_user.id}')):
        bot.answer_callback_query(callback_query.id, text='Вы не ввели номер группы', show_alert=True)
        return
    kb = telebot.types.InlineKeyboardMarkup()
    current_weekday = datetime.datetime.today().weekday()
    for i in enumerate(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']):
        if current_weekday == i[0]:
            kb.row(telebot.types.InlineKeyboardButton(text=f'{i[1]} (Сегодня)',
                                                      callback_data=f'schedule_weekday:{i[1]}'))
        else:
            kb.row(
                telebot.types.InlineKeyboardButton(text=i[1], callback_data=f'schedule_weekday:{i[1]}'))
    btn = telebot.types.InlineKeyboardButton(text='Назад', callback_data='back_to_main')
    kb.row(btn)
    bot.edit_message_text('Выберите день недели', message_id=callback_query.message.message_id,
                          chat_id=callback_query.message.chat.id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m: m.data.startswith('schedule_weekday'))
def get_schedule(callback_query):
    weekday = callback_query.data.split(':')[1]
    connection = db.create_connection()
    try:
        schedule = db.get_or_create_schedule(connection, weekday, redis, callback_query)
        kb = telebot.types.InlineKeyboardMarkup()
        for i in schedule:
            text = f'{i[0]}) {i[2]} {i[1]}'
            btn = telebot.types.InlineKeyboardButton(text=text, callback_data=f'get_info:{i[3]}')
            kb.row(btn)
        btn = telebot.types.InlineKeyboardButton(text='Назад', callback_data='schedule')
        kb.row(btn)
        bot.edit_message_text(
            f'Вы выбрали {weekday.capitalize()}. Можете нажать на предмет, чтобы получить более подробную информацию',
            callback_query.message.chat.id, message_id=callback_query.message.message_id,
            reply_markup=kb)
    except exceptions.MpeiBotException as e:
        bot.answer_callback_query(callback_query.id, e.message, show_alert=True)
    connection.close()


@bot.callback_query_handler(func=lambda x: x.data.startswith('get_info'))
def get_more_information(callback_query: telebot.types.CallbackQuery):
    id_schedule = callback_query.data.split(':')[1]
    kb = callback_query.message
    print(kb)
    bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    try:
        information = db.get_information_about_subject(db.create_connection(), id_schedule)[0]
    except IndexError:
        bot.answer_callback_query(callback_query.id,
                                  text='Хмм... Вы пытаетесь получить старое расписание. Нажмите, пожалуйста, назад и выберите заново день недели',
                                  show_alert=True)
        return

    text = f"""
    День недели:{information[1]}
Номер пары:{information[2]}
Название предмета:{information[3]}
Тип пары:{information[7]}
Преподаватель:{information[6]}
Кабинет:{information[5]}
    """
    bot.send_message(callback_query.message.chat.id, text)


@bot.callback_query_handler(func=lambda m: m.data == 'settings')
def handling_settings(callback_query: telebot.types.CallbackQuery):
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Поменять группу', callback_data='change_group')
    btn2 = telebot.types.InlineKeyboardButton(text='Назад', callback_data='back_to_main')
    kb.row(btn1)
    kb.row(btn2)
    bot.edit_message_text(text='Настройки', reply_markup=kb, chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id)


@bot.callback_query_handler(func=lambda m: m.data == 'change_group')
def change_group(callback_query):
    bot.send_message(callback_query.message.chat.id, text='Введи номер группы')
    redis.set(f'step:{callback_query.from_user.id}', value=SETTINGS_CHANGE_GROUP)


@bot.message_handler(content_types=['text'],
                     func=lambda m: int(redis.get(f'step:{m.from_user.id}').decode('utf8')) == SETTINGS_CHANGE_GROUP)
def get_new_group(message):
    group = message.text.upper()
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='schedule')
    btn2 = telebot.types.InlineKeyboardButton(text='Настройки', callback_data='settings')
    kb.row(btn1)
    kb.row(btn2)
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    try:
        groupoid = parsing.get_groupoid_or_raise_exception(group, redis)
    except exceptions.MpeiBotException as e:
        user_group = redis.get(f'user_group:{message.from_user.id}')
        if user_group:
            user_group = user_group.decode('utf8')
            continue_text = f'студент {user_group} {emoji}'
        else:
            continue_text = f'МЭИшник {emoji}'
        bot.send_message(message.chat.id, text=e.message)
        bot.send_message(message.chat.id, text=f'Привет, {continue_text}', reply_markup=kb)
        return
    redis.set(f'user_groupoid:{message.from_user.id}', value=groupoid)
    redis.set(f'user_group:{message.from_user.id}', value=group)
    redis.set(f'step:{message.from_user.id}', value=START)
    bot.send_message(message.chat.id, 'Вы поменяли группу')
    continue_text = f'студент {group} {emoji}'
    bot.send_message(message.chat.id, f'Привет, {continue_text}', reply_markup=kb)


def main():
    try:
        bot.polling()
    except ApiException as e:
        time.sleep(5)
        logging.fatal(f'{e}')
        main()


if __name__ == '__main__':
    main()
