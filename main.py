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
from services import create_main_keyboard

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(token=TOKEN, skip_pending=True)

redis = redis.Redis()

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    filename='log.log')

START, SETTINGS_CHANGE_GROUP = range(2)


@bot.message_handler(commands=['start'])
def handling_start(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    redis.sadd('unique_users', message.chat.id)
    kb = create_main_keyboard()
    user_group = redis.get(f'user_group:{message.from_user.id}')
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    if user_group:
        user_group = user_group.decode('utf8')
        current_week = redis.get('current_week').decode('utf8')
        continue_text = f'студент {user_group} {emoji}. Сегодня идет {current_week} неделя'
        bot.send_message(message.chat.id, text=f'Привет, {continue_text}', reply_markup=kb)
    else:
        redis.set(f'step:{message.from_user.id}', value=SETTINGS_CHANGE_GROUP)
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_new_group)
        bot.send_message(message.chat.id, 'Привет, Введите, пожалуйста, номер группы')


@bot.callback_query_handler(func=lambda m: m.data == 'back_to_main')
def handling_back_to_main(callback_query):
    bot.clear_step_handler_by_chat_id(callback_query.message.chat.id)
    kb = create_main_keyboard()
    user_group = redis.get(f'user_group:{callback_query.from_user.id}')
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    current_week = redis.get('current_week').decode('utf8')
    if user_group:
        user_group = user_group.decode('utf8')
        continue_text = f'студент {user_group} {emoji}. Сегодня идет {current_week} неделя'
    else:
        continue_text = f'МЭИшник {emoji}. Сегодня идет {current_week} неделя'
    bot.edit_message_text(text=f'Привет, {continue_text}', chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m: m.data.startswith('weekdays'))
def handling_schedule(callback_query):
    what_week = callback_query.data.split(':')[1]
    if not (redis.get(f'user_group:{callback_query.from_user.id}')):
        bot.answer_callback_query(callback_query.id, text='Вы не ввели номер группы', show_alert=True)
        return
    kb = telebot.types.InlineKeyboardMarkup()
    current_weekday = datetime.datetime.today().weekday()
    for i in enumerate(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']):
        if current_weekday == i[0] and what_week == 'current':
            kb.row(telebot.types.InlineKeyboardButton(text=f'{i[1]} (Сегодня)',
                                                      callback_data=f'schedule_weekday:{i[1]}:{what_week}'))
        else:
            kb.row(
                telebot.types.InlineKeyboardButton(text=i[1], callback_data=f'schedule_weekday:{i[1]}:{what_week}'))
    if what_week == 'current':
        btn = telebot.types.InlineKeyboardButton(text=f'Следующая неделя', callback_data='weekdays:next')
    elif what_week == 'next':
        btn = telebot.types.InlineKeyboardButton(text=f'Текущая неделя', callback_data='weekdays:current')
    kb.row(btn)
    btn = telebot.types.InlineKeyboardButton(text='Назад', callback_data='back_to_main')
    kb.row(btn)
    bot.edit_message_text('Выберите день недели', message_id=callback_query.message.message_id,
                          chat_id=callback_query.message.chat.id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m: m.data.startswith('schedule_weekday'))
def get_schedule(callback_query):
    weekday = callback_query.data.split(':')[1]
    what_week = callback_query.data.split(':')[2]
    addition = 0 if what_week == 'current' else 1
    week_num = int(redis.get('current_week').decode('utf8')) + addition
    connection = db.create_connection()
    try:
        schedule = db.get_or_create_schedule(connection, weekday, redis, callback_query, week_num)
        kb = telebot.types.InlineKeyboardMarkup()
        for i in schedule:
            text = f'{i[0]}) {i[2]} {i[1]}'
            btn = telebot.types.InlineKeyboardButton(text=text, callback_data=f'get_info:{i[3]}:{what_week}')
            kb.row(btn)
        btn = telebot.types.InlineKeyboardButton(text='Назад', callback_data=f'weekdays:{what_week}')
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
    what_week = callback_query.data.split(':')[2]
    text_reply = callback_query.message.json['text']
    template_kb = callback_query.message.json['reply_markup']['inline_keyboard']
    kb = telebot.types.InlineKeyboardMarkup()
    kb.keyboard = template_kb
    try:
        information = db.get_information_about_subject(db.create_connection(), id_schedule)[0]
    except IndexError:
        bot.answer_callback_query(callback_query.id,
                                  text='Хмм... Вы пытаетесь получить старое расписание. Нажмите, пожалуйста, назад и \
                                        выберите заново день недели',
                                  show_alert=True)
        return
    time_subj_num = {
        1: '09:20 - 10:55',
        2: '11:10 - 12:45',
        3: '13:45 - 15:20',
        4: '15:35 - 17:10',
        5: '17:20 - 18:50',
        6: '18:55 - 20:25',
    }
    text = f"""
    День недели:{information[1]}
Номер пары:{information[2]}
Название предмета:{information[3]}
Тип пары:{information[7]}
Преподаватель:{information[6]}
Кабинет:{information[5]}
Время пары: {time_subj_num[information[2]]}
    """
    back_keyboard = telebot.types.InlineKeyboardMarkup()
    back_keyboard.row(telebot.types.InlineKeyboardButton(text='Назад',
                                                         callback_data=f'schedule_weekday:{information[1]}:{what_week}'))
    bot.send_message(callback_query.message.chat.id, text, reply_markup=back_keyboard)


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
    bot.answer_callback_query(callback_query.id,text='Введи номер группы', show_alert=True)
    bot.register_next_step_handler_by_chat_id(callback_query.message.chat.id, get_new_group)


def get_new_group(message: telebot.types.Message):
    group = message.text.upper()
    kb = create_main_keyboard()
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    bot.delete_message(message.chat.id, message.message_id)
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
    continue_text = f'студент {group} {emoji}'
    bot.send_message(message.chat.id, f'Привет, {continue_text}', reply_markup=kb)


def main():
    bot.polling()

if __name__ == '__main__':
    main()
