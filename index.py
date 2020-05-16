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
        'description': 'У фильмы, возможно, нелепо переведенное название. Не обращай внимания. "Паразитов" смотрели все. Настало время смотреть другие, более сильные фильмы этого режиссера.',
        'tags': ['Корея', 'легкий хоррор', 'увлекательно']
    },
    {
        'name': 'Теснота',
        'year': 2017,
        'description': 'Это просто очень живое кино, с самой живой героиней. Нальчик конца 90-х, местный колорит, похищение ради выкупа, взросление. Лучший дебютный фильм в российском кино? Возможно.',
        'tags': ['Россия', 'дебют']
    }
]

more_button_text = 'еще'

def get_recommendation(text):
    items_with_tag = []
    if text and not text.startswith('/') and not text == more_button_text:
        items_with_tag = [x for x in items if text in x['tags']]

    if items_with_tag != []:
        item = random.choice(items_with_tag)
    else:
        item = random.choice(items)

    text = f"""
<b>{item['name']}</b>, <i>{item['year']}</i>

{item['description']}
    """

    buttons = item['tags']
    return text, buttons

def get_tags_keyboard(tags):
    keyboard =[[]]

    row = 0
    ind = 0
    for tag in tags:
        keyboard[row].append(InlineKeyboardButton(text=tag, callback_data=tag))
        ind += 1
        # Start next row after 3 tags
        if ind % 3 == 0:
            keyboard.append([])
            row += 1

    return InlineKeyboardMarkup(keyboard)

def reply(bot, message):
    chat_id = message.chat.id
    text, tags = get_recommendation(message.text)
    tags.append(more_button_text)

    bot.sendMessage(chat_id=chat_id,
                    parse_mode='HTML',
                    text=text,
                    reply_markup=get_tags_keyboard(tags))

def reply_to_inline(bot, query):
    text, tags = get_recommendation(query.data)
    tags.append(more_button_text)

    bot.answerCallbackQuery(callback_query_id=query.id)
    bot.sendMessage(chat_id=query.message.chat.id,
                    parse_mode='HTML',
                    text=text,
                    reply_markup=get_tags_keyboard(tags))


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

        if update.message:
            reply(bot, update.message)
        else:
            reply_to_inline(bot, update.callback_query)
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
