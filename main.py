import telebot
import redis

TOKEN = '1190382600:AAFQ1kgr7BqsN-poWciwL8XGQtcTGsbF3kg'

bot = telebot.TeleBot(token=TOKEN)

redis = redis.Redis(host='ec2-34-252-21-252.eu-west-1.compute.amazonaws.com', username='h',
                    password='p1aa776530e62212d009d213615cea336a768fc39815bdde3ee383037db2567b3', port=10509)

START, SETTINGS_CHANGE_GROUP = range(2)


@bot.message_handler(commands=['start'])
def handling_start(message) :
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
    print(redis.get(name='user_group_{message.from_user.id}').decode('utf8'))


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


@bot.message_handler(content_types=['text'], func=lambda m: int(redis.get(f'step_{m.from_user.id}').decode('utf8')) == SETTINGS_CHANGE_GROUP)
def get_new_group(message):
    group = message.text
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
