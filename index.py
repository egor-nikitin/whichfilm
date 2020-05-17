import os
import random
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from flask import Flask, jsonify, Response, request
app = Flask(__name__)


items = [
    {
        'id': 1,
        'name': 'Айка',
        'year': 2018,
        'description': 'Как выжить в Москве нелегальной мигрантке после родов? Жесткое и правдивое кино о современной России. Нам очень не хвататет таких фильмов.',
        'tags': ['Россия', 'социалка', 'драма']
    },
    {
        'id': 2,
        'name': 'Убийство китайского букмекера',
        'year': 1976,
        'description': 'Сразу скажу, кино не для начинающих. Пожалуй, самый увлекательный фильм Кассаветиса. Фирменный ни с чем не сравнимый ультрареализм. Сюжет? Непросто управлять ночным клубом, когда ты в долгах.',
        'tags': ['классика', 'увлекательно', 'долги']
    },
    {
        'id': 3,
        'name': 'Вторжение динозавра',
        'year': 2006,
        'description': 'У фильмы, возможно, нелепо переведенное название. Не обращай внимания. "Паразитов" смотрели все. Настало время смотреть другие, более сильные фильмы этого режиссера.',
        'tags': ['Корея', 'легкий хоррор', 'увлекательно']
    },
    {
        'id': 4,
        'name': 'Теснота',
        'year': 2017,
        'description': 'Это просто очень живое кино, с самой живой героиней. Нальчик конца 90-х, местный колорит, похищение ради выкупа, взросление. Лучший дебютный фильм в российском кино? Возможно.',
        'tags': ['Россия', 'дебют', 'похищение']
    },
    {
        'id': 5,
        'name': 'Место под соснами',
        'year': 2012,
        'description': 'По сути два фильма в одном, хотя погодите. Не будут продавать главный поворот в истории. История мотогонщика-грабителя, которая становится чем-то большим. Ну, и куда без Райана Гослинга.',
        'tags': ['увлекательно', 'мотоциклы', 'драма']
    },
    {
        'id': 6,
        'name': 'Самурай',
        'year': 1967,
        'description': 'История киллера, рассказанная сухо, без эмоций, без единого лишнего кадра. Новичкам смотреть будет непривычно. Но оно того стоит.',
        'tags': ['классика', 'нуар', 'невозмутимость']
    },
    {
        'id': 7,
        'name': 'Неограненные драгоценности',
        'year': 2019,
        'description': 'Вы узнаете, что Адам Сэндлер – отличный драматический актер. Вас будет раздражать чересчур громкий саундтрек. Вас настигнет катарсис в финале. История про ювелира, который больше всего в жизни любит делать ставки.',
        'tags': ['новое', 'электромузыка', 'драма', 'долги']
    },
    {
        'id': 8,
        'name': 'Брачная история',
        'year': 2019,
        'description': 'Истории про развод на удивление увлекательны. Помните, наверное, «Крамер против Крамера» и «Развод Надера и Семин» (его я, признаюсь, не смотрел). Адам Драйвер и Скарлетт Йохансон кричат друг на друга как в последний раз.',
        'tags': ['новое', 'развод', 'драма']
    },
    {
        'id': 9,
        'name': 'Головой об стенку',
        'year': 2003,
        'description': 'Это кино - чистый секс. Молодая турчанка в Германии после очередной попытки самоубийства знакомится в психушке с алкашом-музыкантом и предлагает ему фиктивный брак, чтобы съехать от родителей. Про то, что от родины не сбежишь.',
        'tags': ['страсть', 'фиктивный брак', 'ревность']
    },
    {
        'id': 10,
        'name': 'Верность',
        'year': 2019,
        'description': 'Самый откровенный, честный, открытый фильм про секс, снятый в России. Из тех, на показах которых в кино ползала стыдливо хихикают. Очень. Много. Эротических. Сцен.',
        'tags': ['новое', 'секс', 'свобода', 'ревность', 'Россия']
    },
    {
        'id': 11,
        'name': 'Турецкие сладости',
        'year': 1973,
        'description': 'Из ранних фильмов Пола Верховена. Для него нет никаких запретов и ограничений. Он плевал на правила хорошего тона. В его фильмах ничего не бывает наполовину. Если герой садится в машину, он разобьет ее вдребезги. Если влюбляется – то до конца жизни.',
        'tags': ['страсть', 'свобода', 'ревность'],
        'image_url': 'https://m.media-amazon.com/images/M/MV5BNmI2MTAzOTctYTY2YS00MjFhLWIzZDUtMmQxYWY0NTIxMGQ4XkEyXkFqcGdeQXVyOTc5MDI5NjE@._V1_.jpg'
    },
    {
        'id': 12,
        'name': 'Солнцестояние',
        'year': 2019,
        'description': 'Жуть под яркий шведских солнцем. Подробности странных ритуалов общины улыбщих людей в белой одежде. И молодая компания, которая приезжает погостить и для которой это, понятно, не заканчивается ничем хорошим.',
        'tags': ['новое', 'легкий хоррор', 'травма', 'секта'],
        'image_url': 'https://m.media-amazon.com/images/M/MV5BMzQxNzQzOTQwM15BMl5BanBnXkFtZTgwMDQ2NTcwODM@._V1_SY1000_CR0,0,674,1000_AL_.jpg'
    },
]

more_button_text = 'еще'

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

def send_item(bot, chat, item):
    text = get_item_text(item)
    tags_plus_extra = item['tags'] + [more_button_text]
    if 'image_url' in item:
        bot.sendPhoto(chat_id=chat.id,
                      photo=item['image_url'],
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
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        if update.message:
            reply(bot, update.message)
        else:
            reply_to_inline(bot, update.callback_query)
    else:
        return str(bot.get_me())
        
    return jsonify({"status": "ok"})
