import os

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)
from functools import partial

from store_requests import (add_product_to_cart, create_token,
                            get_all_products, get_cart)

_database = None

def start(update, context, moltin_token):
    products = get_all_products(moltin_token)['data']
    keyboard = [[InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)

    return "ECHO"


def echo(update, context, moltin_token):

    query = update.callback_query

    context.bot.edit_message_text(text="Selected option: {}".format(query.data),
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
    return "ECHO"


def handle_users_reply(update, context, moltin_token):

    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")
    
    states_functions = {
        'START': partial(start, moltin_token=moltin_token),
        'ECHO': partial(echo, moltin_token=moltin_token),
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():

    global _database
    if _database is None:
        database_password = os.getenv("DATABASE_PASSWORD")
        database_host = os.getenv("DATABASE_HOST")
        database_port = os.getenv("DATABASE_PORT")
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    load_dotenv()
    moltin_token = create_token(os.getenv("MOLTIN_CLIENT_ID"))
    tg_token = os.getenv("TG_BOT_TOKEN")
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(partial(handle_users_reply, moltin_token=moltin_token)))
    dispatcher.add_handler(MessageHandler(Filters.text, partial(handle_users_reply, moltin_token=moltin_token)))
    dispatcher.add_handler(CommandHandler('start', partial(handle_users_reply, moltin_token=moltin_token)))
    updater.start_polling()
