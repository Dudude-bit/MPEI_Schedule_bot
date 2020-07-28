import telebot
import redis
import datetime
import db

TOKEN = '1190382600:AAFQ1kgr7BqsN-poWciwL8XGQtcTGsbF3kg'
bot = telebot.TeleBot(token=TOKEN)

redis = redis.Redis()

START, SETTINGS_CHANGE_GROUP = range(2)


@bot.message_handler(commands=['start'])
def handling_start(message) :
    redis.set(f'step_{message.from_user.id}', START)
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='schedule')
    btn2 = telebot.types.InlineKeyboardButton(text='Настройки', callback_data='settings')
    kb.row(btn1)
    kb.row(btn2)
    bot.send_message(message.chat.id, text='Привет, МЭИшник :)', reply_markup=kb)


@bot.callback_query_handler(func=lambda m : m.data == 'back_to_main')
def handling_back_to_main(callback_query) :
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='schedule')
    btn2 = telebot.types.InlineKeyboardButton(text='Настройки', callback_data='settings')
    kb.row(btn1)
    kb.row(btn2)
    bot.edit_message_text(text='Привет, МЭИшник :)', chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m : m.data == 'schedule')
def handling_schedule(callback_query) :
    if not (redis.get(f'user_group_{callback_query.from_user.id}')) :
        bot.answer_callback_query(callback_query.id, text='Вы не ввели номер группы', show_alert=True)
        return
    kb = telebot.types.InlineKeyboardMarkup()
    current_weekday = (datetime.datetime.today() + datetime.timedelta(hours=3)).weekday()
    group_of_user = redis.get(f'user_group_{callback_query.from_user.id}').decode('utf8')
    for i in enumerate(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']) :
        if current_weekday == i[0] :
            kb.row(telebot.types.InlineKeyboardButton(text=f'{i[1]} (Сегодня)',
                                                      callback_data=f'schedule_weekday_{group_of_user}_{i[1]}'))
        else :
            kb.row(
                telebot.types.InlineKeyboardButton(text=i[1], callback_data=f'schedule_weekday_{group_of_user}_{i[1]}'))
    btn = telebot.types.InlineKeyboardButton(text='Назад', callback_data='back_to_main')
    kb.row(btn)
    bot.edit_message_text('Выбери день недели', message_id=callback_query.message.message_id,
                          chat_id=callback_query.message.chat.id, reply_markup=kb)


@bot.callback_query_handler(func=lambda m : m.data.startswith('schedule_weekday'))
def get_schedule(callback_query) :
    _, _, group_of_user, weekday = callback_query.data.split('_')
    connection = db.create_connection()
    try :
        schedule = db.get_or_create_schedule(connection, group_of_user, weekday)
    except IndexError :
        bot.answer_callback_query(callback_query.id,
                                  'Расписание для группы, которую Вы ввели не существует, если же Вы считаете, что ввели все правильно, то напишите, пожалуйста, разработчику.', show_alert=True)


@bot.callback_query_handler(func=lambda m : m.data == 'settings')
def handling_settings(callback_query: telebot.types.CallbackQuery) :
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Поменять группу', callback_data='change_group')
    btn2 = telebot.types.InlineKeyboardButton(text='Назад', callback_data='back_to_main')
    kb.row(btn1)
    kb.row(btn2)
    bot.edit_message_text(text='Настройки', reply_markup=kb, chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id)


@bot.callback_query_handler(func=lambda m : m.data == 'change_group')
def change_group(callback_query) :
    bot.send_message(callback_query.message.chat.id, text='Введи номер группы')
    redis.set(f'step_{callback_query.from_user.id}', value=SETTINGS_CHANGE_GROUP)


@bot.message_handler(content_types=['text'],
                    func=lambda m : int(redis.get(f'step_{m.from_user.id}').decode('utf8')) == SETTINGS_CHANGE_GROUP)
def get_new_group(message) :
    group = message.text.upper()
    redis.set(f'user_group_{message.from_user.id}', value=group)
    redis.set(f'step_{message.from_user.id}', value=START)
    kb = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text='Посмотреть расписание', callback_data='schedule')
    btn2 = telebot.types.InlineKeyboardButton(text='Настройки', callback_data='settings')
    kb.row(btn1)
    kb.row(btn2)
    bot.send_message(message.chat.id, 'Вы поменяли группу')
    bot.send_message(message.chat.id, 'Привет, МЭИшник :)', reply_markup=kb)


bot.polling()
