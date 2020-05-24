import os
import random
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import analytics
import db

from flask import Flask, jsonify, Response, request
app = Flask(__name__)

def init():
    global_ctx = {
        'items': [],
        'chats': {}
    }
    db.init(global_ctx)

    return global_ctx

ctx = init()

def get_recommendation(ctx, chat_id, text):
    filtered__items = ctx['chats'][chat_id]['prev_items'] + ctx['chats'][chat_id]['watched_items']

    items = ctx['items']
    items = [x for x in items if x['id'] not in filtered__items]

    filtered = False
    if text:
        items_with_tag = [x for x in items if text in x['tags']]
        item = random.choice(items_with_tag) if items_with_tag != [] else None
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

def save_sent_item(ctx, chat, item):
    depth = 5
    prev_items = ctx['chats'][chat.id]['prev_items']
    if len(prev_items) == depth:
        prev_items = prev_items[1:]
    ctx['chats'][chat.id]['prev_items'] = prev_items + [item['id']]

def send_item(ctx, bot, user, chat, item):
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
        db.update_item(ctx, item)
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

    save_sent_item(ctx, chat, item)
    analytics.send_item_sent_event(user, chat, item)


def send_start_message(ctx, bot, chat):
    text = 'Я буду советовать фильмы из категорий, которые ты будешь выбирать. Наверное, тебя интересуют новинки. Если нет, могу предложить случайный фильм. Или просто набери интересную тебе категорию. Поищем.'
    tags = ['Хочу новинки', 'Давай случайный']
    bot.sendMessage(chat_id=chat.id,
                    text=text,
                    reply_markup=get_reply_keyboard(tags))

def send_help_message(ctx, bot, chat):
    text = """Советую кино, которое мне самому нравится. Нажимай на любой из тэгов фильма, чтобы увидеть другой с таким же тэгом. Можешь просто набрать тэг текстом.

/start, если хочешь начать разговор сначала.

С предложениями и вопросами можно обращаться к @nikitinev.
"""
    tags = ['Понятно', 'Что посмотреть?']
    bot.sendMessage(chat_id=chat.id,
                    text=text,
                    reply_markup=get_reply_keyboard(tags))            

def send_seen_it_message(ctx, bot, chat):
    text = random.choice(['А ты насмотренный.', 'Ладно. Дай подумать.', 'Бывает. Сейчас еще один дам.', 'А этот?'])
    bot.sendMessage(chat_id=chat.id,
                    text=text)

def send_followup_message(ctx, bot, chat, tag=None):
    text = random.choice(['Ну что, как тебе?', 'Вот такое кино вспомнилось. Что думаешь?', 'Только не говори, что уже смотрел.', 'Что думаешь?'])
    if tag:
        tags = ['Еще ' + tag, 'Другое', 'Смотрел']
    else:
        tags = ['Давай еще', 'Уже смотрел']
    bot.sendMessage(chat_id=chat.id,
                    text=text,
                    reply_markup=get_reply_keyboard(tags))

def send_no_more_items_message(ctx, bot, chat, tag):
    text = 'Все фильмы с темой ' + tag + ' я тебе уже показал. Поэтому держи случайный. Что скажешь?'
    tags = ['Давай еще', 'Уже смотрел']
    bot.sendMessage(chat_id=chat.id,
                    text=text,
                    reply_markup=get_reply_keyboard(tags))

def save_user(ctx, user, chat):
    if db.save_user(ctx, user, chat):
        analytics.send_first_launch_event(user, chat)
    analytics.send_start_event(user, chat)

def reply(ctx, bot, message):
    intent = ''
    if message.text == '/start':
        intent = 'command'
        save_user(ctx, message.from_user, message.chat)
        send_start_message(ctx, bot, message.chat)
    elif message.text == '/help':
        intent = 'command'
        send_help_message(ctx, bot, message.chat)
    else:
        if message.text == 'Хочу новинки':
            intent = 'query'
            text = 'новое'
        elif message.text.lower() in ['уже смотрел', 'смотрел']:
            intent = 'seen_already'
            send_seen_it_message(ctx, bot, message.chat)
            db.save_watched_item(ctx, message.from_user, message.chat)
            text = ''
        elif message.text.startswith('Еще '):
            intent = 'random'
            text = ' '.join(message.text.split(' ')[1:])
        elif message.text.lower() in ['давай случайный', 'другое', 'еще', 'давай еще', 'понятно', 'что посмотреть?'] or message.text.startswith('/'):
            intent = 'random'
            text = ''
        else:
            intent = 'query'
            text = message.text

        item, filtered = get_recommendation(ctx, message.chat.id, text)
        if item:
            send_item(ctx, bot, message.from_user, message.chat, item)
            send_followup_message(ctx, bot, message.chat,
                                  text if filtered else None)
        else:
            item, filtered = get_recommendation(ctx, message.chat.id, '')
            send_item(ctx, bot, message.from_user, message.chat, item)
            send_no_more_items_message(ctx, bot, message.chat, text)

    analytics.send_message_event(message.from_user, message.chat, 'reply', intent, message.text)

def reply_to_inline(ctx, bot, query):
    item, filtered = get_recommendation(ctx, query.message.chat.id, query.data)
    bot.answerCallbackQuery(callback_query_id=query.id)
    if item:
        send_item(ctx, bot, query.from_user, query.message.chat, item)
        send_followup_message(ctx, bot, query.message.chat,
                            query.data if filtered else None)
    else:
        item, filtered = get_recommendation(ctx, query.message.chat.id, '')
        send_item(ctx, bot, query.from_user, query.message.chat, item)
        send_no_more_items_message(ctx, bot, query.message.chat, query.data)

    analytics.send_message_event(query.from_user, query.message.chat, 'inline', 'query', query.data)

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
        random.seed()
        db.refresh_auth(ctx)
        db.update_items_cache(ctx)
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        if update.message:
            db.update_chats_cache(ctx, update.message.from_user, update.message.chat)
            reply(ctx, bot, update.message)
        else:
            db.update_chats_cache(ctx, update.callback_query.from_user, update.callback_query.message.chat)
            reply_to_inline(ctx, bot, update.callback_query)
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
