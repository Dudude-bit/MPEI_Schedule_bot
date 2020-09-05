import telebot
import os
import time

import multiprocessing

TOKEN = os.getenv('TOKEN')
print(TOKEN)
bot = telebot.TeleBot(token=TOKEN)


@bot.message_handler()
def tests(message):
    raise Exceptions()

bot.polling()



