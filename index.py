import os
import random
import logging
import telegram
from telegram import KeyboardButton, ReplyKeyboardMarkup

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

def get_recommendation(text):
    items_with_tag = []
    if text and not text.startswith('/'):
        items_with_tag = [x for x in items if text in x['tags']]

    if items_with_tag != []:
        item = random.choice(items_with_tag)
    else:
        item = random.choice(items)

    return f"""
<b>{item['name']}</b>

Год: {item['year']}

{item['description']}
    """, item['tags']

def get_keyboard(tags):
    keyboard =[[]]
    for tag in tags:
        keyboard[0].append(KeyboardButton(tag))
    return ReplyKeyboardMarkup(keyboard)

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
        text, tags  = get_recommendation(update.message.text)

        bot.sendMessage(chat_id=chat_id,
                        parse_mode='HTML',
                        text=text,
                        reply_markup=get_keyboard(tags))
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
