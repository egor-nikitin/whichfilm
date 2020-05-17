import os
import random
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import pyrebase
import time

from flask import Flask, jsonify, Response, request
app = Flask(__name__)

def init():
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

    return {
        'auth': firebase.auth(),
        'db_auth_updated_at': 0,
        'db_user': {},
        'db': firebase.database(),
        'firebase': firebase,
        'items': []
    }

ctx = init()

def refresh_db_auth(ctx):
    if ctx['db_auth_updated_at'] == 0:
        ctx['db_user'] = ctx['auth'].sign_in_with_email_and_password('yegor.nikitin@gmail.com', 'sdHds3@dkIq8pp')
        ctx['db_auth_updated_at'] = time.time()
    elif (time.time() - ctx['db_auth_updated_at'] > 3500):
        ctx['db_user'] = ctx['auth'].refresh(ctx['db_user']['refreshToken'])
        ctx['db_auth_updated_at'] = time.time()

def update_items_cache(ctx):
    if ctx['items'] == []:
        db_items = ctx['db'].child(ctx['db_user']['localId']).child("items").get(ctx['db_user']['idToken'])
        for db_item in db_items.each():
            item = db_item.val()
            item['id'] = db_item.key()
            ctx['items'].append(item)

def update_item_in_db(ctx, item):
    ctx['db'].child(ctx['db_user']['localId']).child("items").child(item['id']).update(item, ctx['db_user']['idToken'])

def get_recommendation(ctx, input_text):
    text = input_text.lower() if input_text else ''
    items = ctx['items']
    items_with_tag = []
    if text:
        items_with_tag = [x for x in items if text in x['tags']]

    filtered = False
    if items_with_tag != []:
        item = random.choice(items_with_tag)
        filtered = True
    else:
        item = random.choice(items)
    return item, filtered

def split_into_rows(tags):
    rows =[]
    row = -1
    ind = 0
    for tag in tags:
        if ind == 0 or ind >= 3:
            rows.append([])
            row += 1
            ind = 0
        rows[row].append(tag)
        ind += len(tag.split(' '))
    return rows

def get_tags_keyboard(tags):
    rows = split_into_rows(tags)
    keyboard = []
    for row in rows:
        keyboard.append([])
        for tag in row:
            keyboard[-1].append(InlineKeyboardButton(text=tag, callback_data=tag))
    return InlineKeyboardMarkup(keyboard)

def get_reply_keyboard(tags):
    keyboard =[[]]
    for tag in tags:
        keyboard[0].append(KeyboardButton(text=tag))
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

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

def photo_size_to_json(photos):
    images = []
    for photo in photos:
        images.append({
            'file_id': photo.file_id,
            'file_unique_id': photo.file_unique_id,
            'width': photo.width,
            'height': photo.height,
            'file_size': photo.file_size
        })
    return images

def send_item(ctx, bot, chat, item):
    text = get_item_text(item)
    tags = item['tags']
    if not 'file_id' in item and 'image_url' in item:
        message = bot.sendPhoto(chat_id=chat.id,
                      photo=item['image_url'],
                      caption=text,
                      parse_mode='HTML',
                      reply_markup=get_tags_keyboard(tags))
        item['images'] = photo_size_to_json(message.photo)
        item['file_id'] = get_biggest_photo_file_id(message.photo)
        update_item_in_db(ctx, item)
    elif 'file_id' in item:
        bot.sendPhoto(chat_id=chat.id,
                      photo=item['file_id'],
                      caption=text,
                      parse_mode='HTML',
                      reply_markup=get_tags_keyboard(tags))
    else:
        bot.sendMessage(chat_id=chat.id,
                        parse_mode='HTML',
                        text=text,
                        reply_markup=get_tags_keyboard(tags))

def send_start_message(ctx, bot, chat):
    text = 'Я буду советовать фильмы из категорий, которые ты будешь выбирать. Наверное, тебя интересуют новинки. Если нет, могу предложить случайный фильм. Или просто набери интересную тебе категорию. Поищем.'
    tags = ['Хочу новинки', 'Давай случайный']
    bot.sendMessage(chat_id=chat.id,
                    text=text,
                    reply_markup=get_reply_keyboard(tags))

def send_help_message(ctx, bot, chat):
    text = """Советую кино, которое мне самому нравится.

Нажимай на любой из тэгов фильма, чтобы увидеть другой с таким же тэгом. Можешь просто набрать тэг текстом.

/start, если хочешь начать разговор сначала.
"""
    tags = ['Понятно', 'Что посмотреть?']
    bot.sendMessage(chat_id=chat.id,
                    text=text,
                    reply_markup=get_reply_keyboard(tags))            

def send_followup_message(ctx, bot, chat, tag=None):
    text = random.choice(['Ну что, как тебе?', 'Вот такое кино вспомнилось. Что думаешь?', 'Только не говори, что уже смотрел.', 'Что думаешь?'])
    if tag:
        tags = ['Еще ' + tag, 'Что-то другое', 'Смотрел']
    else:
        tags = ['Давай еще', 'Уже смотрел']
    bot.sendMessage(chat_id=chat.id,
                    text=text,
                    reply_markup=get_reply_keyboard(tags))

def send_seen_it_message(ctx, bot, chat):
    text = random.choice(['А ты насмотренный.', 'Ладно. Дай подумать.', 'Бывает. Сейчас еще один дам.', 'А этот?'])
    bot.sendMessage(chat_id=chat.id,
                    text=text)

def reply(ctx, bot, message):
    if message.text == '/start':
        send_start_message(ctx, bot, message.chat)
    elif message.text == '/help':
        send_help_message(ctx, bot, message.chat)
    else:
        if message.text == 'Хочу новинки':
            text = 'новое'
        elif message.text.lower() in ['уже смотрел', 'смотрел']:
            send_seen_it_message(ctx, bot, message.chat)
            text = ''
        elif message.text.startswith('Еще '):
            text = message.text.split(' ')[1]
        elif message.text.lower() in ['давай случайный', 'другое', 'еще', 'давай еще', 'понятно', 'что посмотреть?'] or message.text.startswith('/'):
            text = ''
        else:
            text = message.text
        item, filtered = get_recommendation(ctx, text)
        send_item(ctx, bot, message.chat, item)
        send_followup_message(ctx, bot, message.chat,
                              text if filtered else None)

def reply_to_inline(ctx, bot, query):
    item, filtered = get_recommendation(ctx, query.data)
    bot.answerCallbackQuery(callback_query_id=query.id)
    send_item(ctx, bot, query.message.chat, item)
    send_followup_message(ctx, bot, query.message.chat,
                          query.data if filtered else None)

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
        refresh_db_auth(ctx)
        update_items_cache(ctx)
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        if update.message:
            reply(ctx, bot, update.message)
        else:
            reply_to_inline(ctx, bot, update.callback_query)
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
