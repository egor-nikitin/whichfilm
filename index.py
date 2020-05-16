import os
import random
import logging
import telegram

from flask import Flask, jsonify, Response, request
app = Flask(__name__)


items = [
    {
        'name': 'Айка',
        'year': 2018,
        'description': 'Как выжить в Москве нелегальной мигрантке после родов? Жесткое и правдивое кино о современной России. Нам очень не хвататет таких фильмов.'
    },
    {
        'name': 'Убийство китайского букмекера',
        'year': 1976,
        'description': 'Сразу скажу, кино не для начинающих. Пожалуй, самый увлекательный филь Кассаветиса. Фирменный ни с чем не сравнимый ультрареализм. И неповторимый Бен Газзара.'
    },
    {
        'name': 'Вторжение динозавра',
        'year': 2006,
        'description': 'У фильмы может быть нелепо переведенное название. Не обращайте внимания. "Паразитов" смотрели все. Настало время смотреть другие, более сильные фильмы этого режиссера.'
    },
    {
        'name': 'Теснота',
        'year': 2017,
        'description': 'Бывают фильмы, в которые невозможно не верить. Они передают жизнь. На этот раз – Нальчик конца 90-х. Лучший дебютный фильм в российском кино? Возможно.'
    }
]

def get_recommendation():
    item = random.choice(items)
    return f"""
{item['name']}

Год: {item['year']}

{item['description']}
    """

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

        text = get_recommendation()
        bot.sendMessage(chat_id=chat_id, text=text)
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
