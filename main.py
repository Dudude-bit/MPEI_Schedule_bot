import datetime
import random
import re
import time
import imgkit
import redis
import requests
import telebot
import os
from jinja2 import Template
from prettytable import PrettyTable
from telebot.apihelper import ApiException
from bs4 import BeautifulSoup
import db
import exceptions
import parsing
from services import create_main_keyboard, decorator, generate_subject_text, create_about_keyboard, \
    delete_all_about_bars, saving_user_datas, get_about_text, parsing_marks

time.sleep(10)

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(token=TOKEN, skip_pending=True)

redis = redis.Redis(host='redis')

ALLOWED_BARS_USER_IDS = set(map(int, map(lambda x: x.decode('utf8'), redis.smembers('allowed_users_id'))))
@bot.message_handler(commands=['start'])
@decorator
def handling_start(message):
    user_id = message.from_user.id
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except ApiException:
        pass
    bot.clear_step_handler_by_chat_id(message.chat.id)
    redis.sadd('unique_users', message.chat.id)
    kb = create_main_keyboard(user_id)
    user_group = redis.get(f'user_group:{message.from_user.id}')
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    if user_group:
        user_group = user_group.decode('utf8')
        current_week = redis.get('current_week').decode('utf8')
        continue_text = f'студент {user_group} {emoji}. Сегодня идет {current_week} неделя'
        bot.send_message(message.chat.id, text=f'Привет, {continue_text}', reply_markup=kb)
    else:
        bot.send_message(message.chat.id, 'Привет, Введите, пожалуйста, номер группы')
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_new_group)


@bot.callback_query_handler(func=lambda m: m.data == 'about')
@bot.message_handler(commands=['about'])
def about_handler(message):
    kb = create_about_keyboard()
    count_users = redis.scard('unique_users')
    text = get_about_text(count_users)
    if type(message) == telebot.types.Message:
        bot.send_message(message.chat.id, text, reply_markup=kb, disable_web_page_preview=True)
    else:
        try:
            bot.edit_message_text(text, message.message.chat.id, message.message.message_id,
                                  disable_web_page_preview=True,
                                  reply_markup=kb)
        except ApiException:
            pass


@bot.inline_handler(func=lambda x: True)
def get_schedule_in_chat(inline_query):
    try:
        group, weekday = inline_query.query.split()
        weekday = weekday.lower().capitalize()
    except ValueError:
        return
    th = [weekday]
    try:
        groupoid = parsing.get_groupoid_or_raise_exception(group, redis)
    except exceptions.MpeiBotException:
        return
    connection = db.create_connection()
    try:
        schedule = db.get_or_create_schedule(connection, weekday, re, )
    except:
        return
    table = PrettyTable(th)
    result = telebot.types.InlineQueryResultArticle(inline_query.id, 'Расписание',
                                                    input_message_content=telebot.types.InputTextMessageContent(
                                                        str(table)))
    bot.answer_inline_query(inline_query.id, results=[result])


@bot.callback_query_handler(func=lambda m: m.data == 'call_schedule')
def get_schedule_call(callback_query):
    try:
        bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except ApiException:
        return
    kb = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton('В главное меню', callback_data='back_to_main')
    kb.row(btn)
    sticker_id = 'CAACAgIAAxkBAAIRMF9eFH49vkT2rX5968QLsCcm9NT0AAIBAAOiqcMafGZ5xN8D9x8bBA'
    bot.send_sticker(callback_query.message.chat.id, sticker_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m: m.data == 'bars')
@decorator
def handling_bars(callback_query):
    user_id = callback_query.from_user.id
    if user_id in ALLOWED_BARS_USER_IDS:
        bot.clear_step_handler_by_chat_id(callback_query.message.chat.id)
        session_id = redis.get(f'session_id:{callback_query.from_user.id}')
        if not session_id:
            bot.answer_callback_query(callback_query.id, 'Введите, пожалуйста, логин и пароль в формате ЛОГИН:ПАРОЛЬ',
                                      show_alert=True)
            bot.register_next_step_handler_by_chat_id(callback_query.message.chat.id, change_password_and_username)
        else:
            session_id = session_id.decode('utf8')
            cookies_dict = {
                'auth_bars': session_id
            }
            request = requests.get('https://bars.mpei.ru/bars_web/Student/ListStudent', cookies=cookies_dict)
            if 'ReturnURL' in request.text:
                login = redis.get(f'login:{callback_query.from_user.id}').decode('utf8')
                password = redis.get(f'password:{callback_query.from_user.id}').decode('utf8')
                session = requests.session()
                session.post('https://bars.mpei.ru/bars_web/', data={
                    'UserName': login,
                    'Password': password
                })
                try:
                    session_id = session.cookies.get_dict()['auth_bars']
                    redis.set(f'session_id:{callback_query.from_user.id}', session_id)
                    cookies_dict = {
                        'auth_bars': session_id
                    }
                    text = session.get('https://bars.mpei.ru/bars_web/Student/ListStudent').text
                    a = BeautifulSoup(text, 'lxml').find('tbody').find('tr').find('a').get('href')
                    text = requests.get(f'https://bars.mpei.ru{a}', cookies=cookies_dict).text
                except KeyError:
                    bot.answer_callback_query(callback_query.id,
                                              'Такое ощущение, что у Вас поменялся пароль или логин на аккаунте, либо произошла другая непредвиденная ошибка.')
                    delete_all_about_bars(callback_query, redis)
                    return
            else:
                text = request.text
                a = BeautifulSoup(text, 'lxml').find('tbody').find('tr').find('a').get('href')
                text = requests.get(f'https://bars.mpei.ru{a}', cookies=cookies_dict).text
            bs = BeautifulSoup(text, 'lxml')
            all_subjects = bs.find('div', id='div-Student_SemesterSheet').find_all('div', class_='my-2')
            subjects_list = []
            for item in all_subjects:
                parsing_marks(item, subjects_list)

            with open('bars_template.html') as f:
                templ = Template(f.read())
            color_dict = {
                '5': 'green',
                '4': 'yellow',
                '3': 'orange',
                '2': 'red',
                '1': 'red',
                '0': 'red',
                '': 'grey'
            }
            html_text = templ.render(subjects_list=subjects_list, color_dict=color_dict)
            img = imgkit.from_string(html_text, False)
            bot.send_photo(callback_query.message.chat.id, img)
    else:
        bot.answer_callback_query(callback_query.id,
                                  "Эта функция доступна ограниченному числу лиц. Если Вы хотите получить доступ, то напишити мне в ВК, ссылка есть в разделе 'О Боте'",
                                  show_alert=True)



@bot.callback_query_handler(func=lambda m: m.data == 'back_to_main')
@decorator
def handling_back_to_main(callback_query):
    user_id = callback_query.from_user.id
    bot.clear_step_handler_by_chat_id(callback_query.message.chat.id)
    kb = create_main_keyboard(user_id)
    user_group = redis.get(f'user_group:{callback_query.from_user.id}')
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    current_week = redis.get('current_week').decode('utf8')
    if user_group:
        user_group = user_group.decode('utf8')
        continue_text = f'студент {user_group} {emoji}. Сегодня идет {current_week} неделя'
    else:
        continue_text = f'МЭИшник {emoji}. Сегодня идет {current_week} неделя'
    try:
        bot.edit_message_text(text=f'Привет, {continue_text}', chat_id=callback_query.message.chat.id,
                              message_id=callback_query.message.message_id, reply_markup=kb)
    except ApiException as e:
        result = e.result.json()
        if result['description'] == "Bad Request: message can't be edited":
            try:
                bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            except ApiException:
                return
            bot.send_message(text=f'Привет, {continue_text}', chat_id=callback_query.message.chat.id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m: m.data.startswith('weekdays'))
@decorator
def handling_schedule(callback_query):
    what_week = callback_query.data.split(':')[1]
    if not (redis.get(f'user_group:{callback_query.from_user.id}')):
        bot.answer_callback_query(callback_query.id, text='Вы не ввели номер группы', show_alert=True)
        return
    kb = telebot.types.InlineKeyboardMarkup()
    time_obj = datetime.datetime.today() + datetime.timedelta(
        hours=3)  # Из за разницы во времени на сервере прибавляем 3 часа
    current_weekday = time_obj.weekday()
    for i in enumerate(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']):
        if current_weekday == i[0] and what_week == 'current':
            kb.row(telebot.types.InlineKeyboardButton(text=f'{i[1]} (Сегодня)',
                                                      callback_data=f'schedule_weekday:{i[1]}:{what_week}'))
        else:
            kb.row(
                telebot.types.InlineKeyboardButton(text=i[1], callback_data=f'schedule_weekday:{i[1]}:{what_week}'))
    btn = telebot.types.InlineKeyboardButton(text=f'Текущая неделя',
                                             callback_data='weekdays:current') if what_week == 'next' \
        else telebot.types.InlineKeyboardButton(
        text=f'Следующая неделя', callback_data='weekdays:next')
    kb.row(btn)
    btn = telebot.types.InlineKeyboardButton(text='В главное меню', callback_data='back_to_main')
    kb.row(btn)
    try:
        bot.edit_message_text('Выберите день недели', message_id=callback_query.message.message_id,
                              chat_id=callback_query.message.chat.id, reply_markup=kb)
    except ApiException:
        pass


@bot.callback_query_handler(func=lambda m: m.data.startswith('schedule_weekday'))
@decorator
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
            print(i)
            text = f'{i.num_object}) {i.object} {i.auditory}'
            btn = telebot.types.InlineKeyboardButton(text=text, callback_data=f'get_info:{i.slug}:{what_week}')
            kb.row(btn)
        btn = telebot.types.InlineKeyboardButton(text='Назад', callback_data=f'weekdays:{what_week}')
        kb.row(btn)
        try:
            bot.edit_message_text(
                f'Вы выбрали {weekday.capitalize()}. Можете нажать на предмет, чтобы получить более подробную информацию',
                callback_query.message.chat.id, message_id=callback_query.message.message_id,
                reply_markup=kb)
        except ApiException:
            pass
    except exceptions.MpeiBotException as e:
        bot.answer_callback_query(callback_query.id, e.message, show_alert=True)


@bot.callback_query_handler(func=lambda x: x.data.startswith('get_info'))
@decorator
def get_more_information(callback_query: telebot.types.CallbackQuery):
    id_schedule = callback_query.data.split(':')[1]
    template_kb = callback_query.message.json['reply_markup']['inline_keyboard']
    kb = telebot.types.InlineKeyboardMarkup()
    kb.keyboard = template_kb
    try:
        information = db.get_information_about_subject(db.create_connection(), id_schedule)[0]
    except IndexError:
        bot.answer_callback_query(callback_query.id,
                                  text='Хмм... Вы пытаетесь получить старое расписание. Нажмите, пожалуйста, назад и выберите заново день недели',
                                  show_alert=True)
        return
    text = generate_subject_text(information)
    try:
        bot.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
                              reply_markup=kb)
    except ApiException:
        pass


@bot.callback_query_handler(func=lambda m: m.data == 'change_group')
@decorator
def change_group(callback_query):
    bot.answer_callback_query(callback_query.id, text='Введи номер группы', show_alert=True)
    bot.register_next_step_handler_by_chat_id(callback_query.message.chat.id, get_new_group)


@bot.callback_query_handler(func=lambda m: m.data == 'add_user')
@decorator
def add_user_to_allowed_list(callback_query):
    bot.answer_callback_query(callback_query.id, text='Введите id пользователя', show_alert=True)
    bot.register_next_step_handler_by_chat_id(callback_query.message.chat.id, add_user)


def add_user(message):
    try:
        user_id = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, 'Вы неправильно ввели user id')
    else:
        redis.sadd('allowed_users_id', user_id)
        ALLOWED_BARS_USER_IDS.add(user_id)


@decorator
def get_new_group(message: telebot.types.Message):
    group = message.text
    user_id = message.from_user.id
    if group:
        group = group.upper()
    else:
        return
    kb = create_main_keyboard(user_id)
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
    current_week = redis.get('current_week').decode('utf8')
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except ApiException:
        pass
    try:
        groupoid = parsing.get_groupoid_or_raise_exception(group, redis)
    except exceptions.MpeiBotException as e:
        user_group = redis.get(f'user_group:{message.from_user.id}')
        if user_group:
            user_group = user_group.decode('utf8')
            continue_text = f'студент {user_group} {emoji}. Сегодня идет {current_week} неделя'
        else:
            continue_text = f'МЭИшник {emoji}. Сегодня идет {current_week} неделя'
        bot.send_message(message.chat.id, text=e.message)
        bot.send_message(message.chat.id, text=f'Привет, {continue_text}', reply_markup=kb)
        return
    redis.set(f'user_groupoid:{message.from_user.id}', value=groupoid)
    redis.set(f'user_group:{message.from_user.id}', value=group)
    continue_text = f'студент {group} {emoji}. Сегодня идет {current_week} неделя'
    bot.send_message(message.chat.id, f'Привет, {continue_text}', reply_markup=kb)


def change_password_and_username(message):
    temp_list = message.text.split(':')
    if len(temp_list) != 2:
        bot.send_message(message.chat.id, 'Хмм... Походу Вы в неправильном формате ввели логин и пароль')
        handling_start(message)
    else:
        login, password = temp_list
        session = requests.session()
        session.post('https://bars.mpei.ru/bars_web/', data={
            'UserName': login,
            'Password': password
        })
        try:
            session_id = session.cookies.get_dict()['auth_bars']
        except KeyError:
            bot.send_message(message.chat.id, 'Хмм... Походу Вы ввели неправильно логин или пароль')
            handling_start(message)
        else:
            bot.send_message(message.chat.id,
                             'Вы правильно ввели логин и пароль, теперь Вы можете посмотреть свой БАРС')
            saving_user_datas(message, redis, login, password, session_id)
            handling_start(message)


if __name__ == '__main__':
    bot.polling()
