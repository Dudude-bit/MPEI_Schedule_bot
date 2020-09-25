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


def create_main_keyboard(user_id):
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='weekdays:current')
    btn2 = telebot.types.InlineKeyboardButton(text='Поменять группу', callback_data='change_group')
    btn3 = telebot.types.InlineKeyboardButton(text='Расписание звонков', callback_data='call_schedule')
    btn4 = telebot.types.InlineKeyboardButton(text='БАРС', callback_data='bars')
    btn5 = telebot.types.InlineKeyboardButton(text='О боте', callback_data='about')
    kb.row(btn1)
    kb.row(btn2, btn3)
    kb.row(btn4)
    kb.row(btn5)
    if user_id == 449030562:
        btn6 = telebot.types.InlineKeyboardButton(text='Добавить пользователя', callback_data='add_user')
        kb.row(btn6)
    return kb


def decorator(func):
    def wrapper(message):
        print(datetime.datetime.now())
        return func(message)
    return wrapper


def generate_subject_text(information):
    time_subj_num = {
        1: '09:20 - 10:55',
        2: '11:10 - 12:45',
        3: '13:45 - 15:20',
        4: '15:35 - 17:10',
        5: '17:20 - 18:50',
        6: '18:55 - 20:25',
        7: '20:30 - 22:00'
    }
    return f"""
    День недели:{information.weekday}
Номер пары:{information.num_object}
Название предмета:{information.object}
Тип пары:{information.object_type}
Преподаватель:{information.teacher}
Кабинет:{information.auditory}
Время пары: {time_subj_num[information.num_object]}
    """

def create_about_keyboard():
    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
    btn1 = telebot.types.InlineKeyboardButton(text='Telegram', url='https://t.me/Justnikcname')
    btn2 = telebot.types.InlineKeyboardButton(text='Vk', url='https://vk.com/kirillinyakin')
    btn3 = telebot.types.InlineKeyboardButton(text='GitHub', url='https://github.com/Dudude-bit/MPEI_Schedule_bot')
    btn4 = telebot.types.InlineKeyboardButton(text='DonationAlerts', url='https://www.donationalerts.com/r/userelliot')
    btn5 = telebot.types.InlineKeyboardButton(text='В главное меню', callback_data='back_to_main')
    kb.add(btn1, btn2, btn3, btn4, btn5)
    return kb

def delete_all_about_bars(callback_query, redis):
    redis.delete(f'session_id:{callback_query.from_user.id}')
    redis.delete(f'login:{callback_query.from_user.id}')
    redis.delete(f'password:{callback_query.from_user.id}')


def saving_user_datas(message, redis, login, password, session_id):
    redis.set(f'session_id:{message.from_user.id}', session_id)
    redis.set(f'login:{message.from_user.id}', login)
    redis.set(f'password:{message.from_user.id}', password)


def get_about_text(count_users):
    return f"""
    Привет, этим ботом пользуются {count_users} студентов! Если Вы хотите со мной связаться, то вот мои контакты:
TG: https://t.me/Justnikcname
VK: https://vk.com/kirillinyakin
Если вдруг захотите посмотреть на мой код и улучшить его, так как я только начинаю хоть что то серьезное делать, то вот ссылка на GitHub:
GitHub: https://github.com/Dudude-bit/MPEI_Schedule_bot
Ну а если Вы вдруг захотите оплатить мой сервер, на котором держится этот бот(всего лишь 40 рублей в месяц XD), то вот ссылка на DonationAlerts:
DonationAlerts: https://www.donationalerts.com/r/userelliot
Спасибо за то, что пользуетесь моим ботом ))
    """

def parsing_marks(item, subjects_list):
    name_subject = item.find('strong').text.replace('Дисциплина', '').replace('\"', '').strip()
    table = item.find_next_sibling()
    regex = '\d{1,2}. [а-яА-я]+'
    all_tds_with_km = table.find_all('td', text=re.compile(regex))
    text_all_tds_with_km = [i.text.strip() for i in all_tds_with_km]
    km_num = len(text_all_tds_with_km)
    subjects_list.append({})
    subjects_list[-1]['name'] = name_subject
    subjects_list[-1]['km_num'] = km_num
    subjects_list[-1]['marks'] = []
    for i in range(km_num):
        mark = all_tds_with_km[i].find_next_siblings()[-1].text.strip().split()
        subjects_list[-1]['marks'].append(mark[0] if len(mark) > 0 else '')