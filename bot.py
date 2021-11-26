import os
from functools import partial

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

from store_requests import (add_product_to_cart, create_customer, create_token,
                            delete_product_from_cart, get_all_products,
                            get_cart, get_product,
                            get_product_image)

_database = None


def make_cart_description(cart):

    cart_description = ""
    for product in cart['data']:
        product_description = \
            "{name}\n{description}\n{price} per unit\n{quantity} pcs. in cart for {total_price}\n\n".format(
                name=product['name'],
                price=product['meta']['display_price']['with_tax']['unit']['formatted'],
                total_price=product['meta']['display_price']['with_tax']['value']['formatted'],
                quantity=product['quantity'],
                description=product['description']
            )   
        cart_description += product_description
    cart_description += f"Total: {cart['meta']['display_price']['with_tax']['formatted']}"

    return cart_description


def start(update, context, moltin_token):
    products = get_all_products(moltin_token)['data']
    keyboard = [[InlineKeyboardButton(product['name'], callback_data=product['id'])] for product in products]
    keyboard.append([InlineKeyboardButton('Cart', callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['products_keyboard'] = reply_markup

    update.message.reply_text('Please choose:', reply_markup=reply_markup)

    return "HANDLE_MENU"


def handle_menu(update, context, moltin_token):

    query = update.callback_query

    if query.data == 'cart':
        cart = get_cart(token=moltin_token, cart_id=query.message.chat_id)
        
        cart_description = make_cart_description(cart)
        
        keyboard = [[InlineKeyboardButton(f"Remove {product['name']}", callback_data=product['id'])] for product in cart['data']]

        keyboard.append([InlineKeyboardButton('Back to menu', callback_data='menu')])
        keyboard.append([InlineKeyboardButton('Pay', callback_data='pay')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(text=cart_description, reply_markup=reply_markup)
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        return "HANDLE_CART"

    product_id = query.data
    product = get_product(moltin_token, product_id)['data']

    image_id = product['relationships']['main_image']['data']['id']
    image_link = get_product_image(moltin_token, image_id)['data']['link']['href']

    product_description = "{name}\n\n{price} per unit\n{amount} pcs. available\n\n{description}".format(
        name=product['name'],
        price=product['meta']['display_price']['with_tax']['formatted'],
        amount=product['meta']['stock']['level'],
        description=product['description']
    )
    context.user_data['chosen_product'] = product_id
    keyboard = [[InlineKeyboardButton(f'Buy {pcs}', callback_data=pcs) for pcs in [1, 5, 10]],
                [InlineKeyboardButton('Cart', callback_data='cart'), InlineKeyboardButton('Back', callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_photo(
        caption=product_description,
        photo=image_link,
        chat_id=query.message.chat_id,
        reply_markup=reply_markup
    )
    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )

    return "HANDLE_DESCRIPTION"


def handle_description(update, context, moltin_token):

    query = update.callback_query

    if query.data == 'back':
        query.message.reply_text('Please choose:', reply_markup=context.user_data['products_keyboard'])
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        return "HANDLE_MENU"

    if query.data.isdigit():
        add_product_to_cart(
            token=moltin_token,
            cart_id=query.message.chat_id,
            product_id=context.user_data['chosen_product'],
            quantity=int(query.data)
        )
        return "HANDLE_DESCRIPTION"

    if query.data == 'cart':
        cart = get_cart(token=moltin_token, cart_id=query.message.chat_id)
        
        cart_description = make_cart_description(cart)
        
        keyboard = [[InlineKeyboardButton(f"Remove {product['name']}", callback_data=product['id'])] for product in cart['data']]

        keyboard.append([InlineKeyboardButton('Back to menu', callback_data='menu')])
        keyboard.append([InlineKeyboardButton('Pay', callback_data='pay')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(text=cart_description, reply_markup=reply_markup)
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        return "HANDLE_CART"


def handle_cart(update, context, moltin_token):

    query = update.callback_query

    if query.data == 'pay':
        query.message.reply_text('Send e-mail please for futher purchase')
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
        return "WAITING_EMAIL"

    if query.data != 'menu':
        delete_product_from_cart(
            token=moltin_token,
            cart_id=query.message.chat_id,
            product_id=query.data,
        )

    query.message.reply_text('Product removed. Choose another one:', reply_markup=context.user_data['products_keyboard'])
    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )
    return "HANDLE_MENU"


def handle_email(update, context, moltin_token):
    create_customer(
        token=moltin_token,
        email=update.message.text,
        chat_id=update.message.chat_id,
    )
    update.message.reply_text('We will connect with you soon!')
    return "START"


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
        'HANDLE_MENU': partial(handle_menu, moltin_token=moltin_token),
        'HANDLE_DESCRIPTION': partial(handle_description, moltin_token=moltin_token),
        'HANDLE_CART': partial(handle_cart, moltin_token=moltin_token),
        'WAITING_EMAIL': partial(handle_email, moltin_token=moltin_token),
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
