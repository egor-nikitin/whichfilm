import os
import random
import logging
import telegram
from telegram.error import Unauthorized
import db
import reply
import messages

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

@app.route('/', methods=['GET'])
def getme():
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_NEW')
    bot = telegram.Bot(TELEGRAM_TOKEN)
    return str(bot.get_me())    

@app.route('/clear_items_cache', methods=['GET'])
def clear_cache():
    ctx['items'] = []
    return jsonify({'status': 'ok'})

@app.route('/send_messages', methods=['GET'])
def send_messages():
    messages.send()
    return jsonify({'status': 'ok'})

@app.route('/api2', methods=['GET', 'POST'])
def api():
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_NEW')
    if TELEGRAM_TOKEN is None:
        return jsonify({'status': 'error', 'reason': 'no tg token'})
    
    bot = telegram.Bot(TELEGRAM_TOKEN)
    
    if request.method == 'POST':
        random.seed()
        db.refresh_auth(ctx)
        db.update_items_cache(ctx)
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        if update.message:
            db.update_chats_cache(ctx, update.message.from_user, update.message.chat)
            try:
                reply.reply(ctx, bot, update.message)
            except Unauthorized:
                reply.remove_chat(ctx, update.message.from_user, update.message.chat)
        else:
            db.update_chats_cache(ctx, update.callback_query.from_user, update.callback_query.message.chat)
            try:
                reply.reply_to_inline(ctx, bot, update.callback_query)
            except Unauthorized:
                reply.remove_chat(ctx, update.callback_query.from_user, update.callback_query.message.chat)
    else:
        return str(bot.get_me())
        
    return jsonify({'status': 'ok'})
