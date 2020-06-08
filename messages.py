import db
import reply
from flask import jsonify

#{
#    'users': [123, 456],
#    'offset': 0,
#    'limit': 10,
#    'messages': [{
#        'text': 'aaaa',
#        'inline_tags': ['1', '2', '3'],
#        'reply_tags': ['reply_1', 'reply_2']
#    }]
#}

def send(ctx, bot, request):
    if not 'messages' in request:
        return jsonify({'text': 'No messages to send!'})

    users = db.get_users(ctx)

    # Filter users
    if 'users' in request:
        users = [x for x in users if x['id'] in request['users']]
    users = [x for x in users if 'chat_id' in x]

    # Apply offset and limit
    users.sort(key=lambda x: x['id'])
    if 'offset' in request:
        users = users[request['offset']:]

    if 'limit' in request:
        users = users[:request['limit']]
 

    messages_sent = 0
    users_count = 0
    error_count = 0
    error_texts = []

    for user in users:
        try:
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
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            error_texts.append(template.format(type(ex).__name__, ex.args))
            error_count += 1

        users_count += 1

    return jsonify({
        'messages_sent': messages_sent, 
        'users_count': users_count,
        'error_count': error_count,
        'error_texts': error_texts
    })
