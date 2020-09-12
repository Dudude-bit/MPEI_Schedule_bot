import datetime
import random
import redis
import telebot
import os
from telebot.apihelper import ApiException

import db
import exceptions
import parsing
from services import create_main_keyboard, decorator

TOKEN = os.getenv('TOKENTEST')
bot = telebot.TeleBot(token=TOKEN, skip_pending=True)

redis = redis.Redis()


@bot.message_handler(commands=['start'])
@decorator
def handling_start(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except ApiException:
        pass
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
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_new_group)
        bot.send_message(message.chat.id, 'Привет, Введите, пожалуйста, номер группы')
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_new_group)


@bot.callback_query_handler(func=lambda m: m.data == 'about')
@bot.message_handler(commands=['about'])
def about_handler(message):
    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
    btn1 = telebot.types.InlineKeyboardButton(text='Telegram', url='https://t.me/Justnikcname')
    btn2 = telebot.types.InlineKeyboardButton(text='Vk', url='https://vk.com/kirillinyakin')
    btn3 = telebot.types.InlineKeyboardButton(text='GitHub', url='https://github.com/Dudude-bit/MPEI_Schedule_bot')
    btn4 = telebot.types.InlineKeyboardButton(text='DonationAlerts', url='https://www.donationalerts.com/r/userelliot')
    btn5 = telebot.types.InlineKeyboardButton(text='В главное меню', callback_data='back_to_main')
    count_users = redis.scard('unique_users')
    kb.add(btn1, btn2, btn3, btn4, btn5)
    text = f"""
    Привет, этим ботом пользуются {count_users} студентов! Если Вы хотите со мной связаться, то вот мои контакты:
TG: https://t.me/Justnikcname
VK: https://vk.com/kirillinyakin
Если вдруг захотите посмотреть на мой код и улучшить его, так как я только начинаю хоть что то серьезное делать, то вот ссылка на GitHub:
GitHub: https://github.com/Dudude-bit/MPEI_Schedule_bot
Ну а если Вы вдруг захотите оплатить мой сервер, на котором держится этот бот(всего лишь 40 рублей в месяц XD), то вот ссылка на DonationAlerts:
DonationAlerts: https://www.donationalerts.com/r/userelliot
Спасибо за то, что пользуетесь моим ботом ))
    """
    if type(message) == telebot.types.Message:
        bot.send_message(message.chat.id, text, reply_markup=kb, disable_web_page_preview=True)
    else:
        try:
            bot.edit_message_text(text, message.message.chat.id, message.message.message_id,
                                  disable_web_page_preview=True,
                                  reply_markup=kb)
        except ApiException:
            pass


@bot.callback_query_handler(func=lambda m: m.data == 'back_to_main')
@decorator
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
    try:
        bot.edit_message_text(text=f'Привет, {continue_text}', chat_id=callback_query.message.chat.id,
                              message_id=callback_query.message.message_id, reply_markup=kb)
    except ApiException:
        pass


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
    btn = telebot.types.InlineKeyboardButton(text='Назад', callback_data='back_to_main')
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
            text = f'{i[0]}) {i[2]} {i[1]}'
            btn = telebot.types.InlineKeyboardButton(text=text, callback_data=f'get_info:{i[3]}:{what_week}')
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
        7: '20:30 - 22:00'
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


@decorator
def get_new_group(message: telebot.types.Message):
    group = message.text
    if group:
        group = group.upper()
    else:
        return
    kb = create_main_keyboard()
    emoji_list = list('😀😃😄😊🙃👽🤖🤪😝')
    emoji = random.choice(emoji_list)
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


if __name__ == '__main__':
    bot.polling()
