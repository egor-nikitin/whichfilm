import os
import random
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import pyrebase
import time

from flask import Flask, jsonify, Response, request
app = Flask(__name__)

config = {
    'apiKey': 'AIzaSyA2LihYUsMhVdZa60XBSZ3j4IUaSGh0NOI',
    'authDomain': 'whichfilmbot.firebaseapp.com',
    'databaseURL': 'https://whichfilmbot.firebaseio.com',
    'projectId': 'whichfilmbot',
    'storageBucket': 'whichfilmbot.appspot.com',
    'messagingSenderId': '914533040757',
    'appId': '1:914533040757:web:6410e7bf9f046353cc2e3c'
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db_auth_updated_at = None
db_user = {}
db = firebase.database()

def refresh_db_auth():
    if not db_auth_updated_at:
        db_user = auth.sign_in_with_email_and_password('yegor.nikitin@gmail.com', 'sdHds3@dkIq8pp')
        db_auth_updated_at = time.time()
    elif (time.time() - db_auth_updated_at > 3500):
        db_user = auth.refresh(db_user['refreshToken'])
        db_auth_updated_at = time.time()

items = []
more_button_text = 'еще'

def update_items_cache():
    if items == []:
        db_items = db.child(db_user['localId']).child("items").get(db_user['idToken'])
        for db_item in db_items:
            item = db_item.val()
            item['id'] = db_item.key()
            items.append(item)

def update_item_in_db(item):
    db.child(db_user['localId']).child("items").child(item['id']).update(item, db_user['idToken'])

def get_recommendation(text):
    items_with_tag = []
    if text and not text.startswith('/') and text != more_button_text:
        items_with_tag = [x for x in items if text in x['tags']]

    if items_with_tag != []:
        item = random.choice(items_with_tag)
    else:
        item = random.choice(items)
    return item

def get_tags_keyboard(tags):
    keyboard =[]
    row = -1
    ind = 0
    for tag in tags:
        if ind % 3 == 0:
            keyboard.append([])
            row += 1
        keyboard[row].append(InlineKeyboardButton(text=tag, callback_data=tag))
        ind += 1

    return InlineKeyboardMarkup(keyboard)

def get_item_text(item):
    return f"""
<b>{item['name']}</b>, <i>{item['year']}</i>

{item['description']}
    """

def get_biggest_photo_file_id(photos):
    max_width = 0
    file_id = 0
    for photo in photos:
        if photo.width > max_width:
            max_width = photo.width
            file_id = photo.file_id
    return file_id

def send_item(bot, chat, item):
    text = get_item_text(item)
    tags_plus_extra = item['tags'] + [more_button_text]
    if not 'file_id' in item and 'image_url' in item:
        message = bot.sendPhoto(chat_id=chat.id,
                      photo=item['image_url'],
                      caption=text,
                      parse_mode='HTML',
                      reply_markup=get_tags_keyboard(tags_plus_extra))
        item['photo'] = message.photo
        item['file_id'] = get_biggest_photo_file_id(message.photo)
        update_item_in_db(item)
    elif 'file_id' in item:
        bot.sendPhoto(chat_id=chat.id,
                      photo=item['file_id'],
                      caption=text,
                      parse_mode='HTML',
                      reply_markup=get_tags_keyboard(tags_plus_extra))
    else:
        bot.sendMessage(chat_id=chat.id,
                        parse_mode='HTML',
                        text=text,
                        reply_markup=get_tags_keyboard(tags_plus_extra))

def reply(bot, message):
    item = get_recommendation(message.text)
    send_item(bot, message.chat, item)

def reply_to_inline(bot, query):
    item = get_recommendation(query.data)
    bot.answerCallbackQuery(callback_query_id=query.id)
    send_item(bot, query.message.chat, item)

@app.route('/', methods=['GET'])
def getme():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    bot = telegram.Bot(TELEGRAM_TOKEN)
    return str(bot.get_me())    

@app.route('/api', methods=['GET', 'POST'])
def api():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    if TELEGRAM_TOKEN is None:
        return jsonify({"status": "error", "reason": "no tg token"})
    
    bot = telegram.Bot(TELEGRAM_TOKEN)
    
    if request.method == "POST":
        refresh_db_auth()
        update_items_cache()
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        if update.message:
            reply(bot, update.message)
        else:
            reply_to_inline(bot, update.callback_query)
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
