import os
import random
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from flask import Flask, jsonify, Response, request
app = Flask(__name__)


items = [
    {
        'name': 'Айка',
        'year': 2018,
        'description': 'Как выжить в Москве нелегальной мигрантке после родов? Жесткое и правдивое кино о современной России. Нам очень не хвататет таких фильмов.',
        'tags': ['Россия', 'социалка', 'драма']
    },
    {
        'name': 'Убийство китайского букмекера',
        'year': 1976,
        'description': 'Сразу скажу, кино не для начинающих. Пожалуй, самый увлекательный фильм Кассаветиса. Фирменный ни с чем не сравнимый ультрареализм. Сюжет? Непросто управлять ночным клубом, когда ты в долгах.',
        'tags': ['классика', 'увлекательно']
    },
    {
        'name': 'Вторжение динозавра',
        'year': 2006,
        'description': 'У фильмы может быть нелепо переведенное название. Не обращайте внимания. "Паразитов" смотрели все. Настало время смотреть другие, более сильные фильмы этого режиссера.',
        'tags': ['Корея', 'легкий хоррор', 'увлекательно']
    },
    {
        'name': 'Теснота',
        'year': 2017,
        'description': 'Это просто очень живое кино, с самой живой героиней. Нальчик конца 90-х, местный колорит, похищение ради выкупа, взросление. Лучший дебютный фильм в российском кино? Возможно.',
        'tags': ['Россия', 'дебют']
    }
]

def get_recommendation(callback_query):
    if callback_query:
        tag = callback_query.data
        items_with_tag = [x for x in items if tag in x['tags']]
        item = random.choice(items_with_tag)
    else:
        item = random.choice(items)

    return f"""
**{item['name']}**

Год: {item['year']}

{item['description']}
    """, item['tags']

def get_keyboard(tags):
    keyboard =[[]]
    for tag in tags:
        keyboard[0].append(InlineKeyboardButton(tag, callback_data=tag))
    return InlineKeyboardMarkup(keyboard)

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
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        chat_id = update.message.chat.id

        text, tags  = get_recommendation(update.callback_query)

        if update.callback_query:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id)

        bot.sendMessage(chat_id=chat_id, text=text, reply_markup=get_keyboard(tags))
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
