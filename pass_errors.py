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

<<<<<<< HEAD


=======
process = multiprocessing.Process(target=bot.polling)
process.start()
>>>>>>> 5b0f9a7effbb484c382d517bb541dc54c8adfdc3
