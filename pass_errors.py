import telebot
import os
import time

import multiprocessing

TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(token=TOKEN)


@bot.message_handler()
def tests(message):
    pass


process = multiprocessing.Process(target=bot.polling)
process.start()

time.sleep(10)

process.kill()
