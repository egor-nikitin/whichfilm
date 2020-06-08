import db
import reply
from flask import jsonify

#{
#    'users': [123, 456],
#    'messages': [{
#        'text': 'aaaa',
#        'inline_tags': ['1', '2', '3'],
#        'reply_tags': ['reply_1', 'reply_2']
#    }]
#}

def send(ctx, bot, request):
    if not 'messages' in request:
        return jsonify({'text': 'No messages to send!'})

    users_filter = []
    if 'users' in request:
        users_filter = request['users']

    users = db.get_users(ctx)
    messages_sent = 0
    users_count = 0

    for user in users:
        # Filter users
        if 'chat_id' not in user:
            continue
        if users_filter and user['id'] not in users_filter:
            continue

        for message in request['messages']:
            if 'inline_tags' in message:
                bot.sendMessage(chat_id=user['chat_id'],
                                parse_mode='HTML',
                                text=message['text'],
                                reply_markup=reply.get_tags_keyboard(message['inline_tags']))
                messages_sent += 1
            elif 'reply_tags' in message:
                bot.sendMessage(chat_id=user['chat_id'],
                                parse_mode='HTML',
                                text=message['text'],
                                reply_markup=reply.get_reply_keyboard(message['reply_tags']))
                messages_sent += 1
            else:
                bot.sendMessage(chat_id=user['chat_id'],
                                parse_mode='HTML',
                                text=message['text'])
                messages_sent += 1
        
        users_count += 1

    return jsonify({'messages_sent': messages_sent, 'users_count': users_count})
