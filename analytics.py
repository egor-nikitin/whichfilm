import requests
import uuid
import datetime
import os

headers = {
  'Content-Type': 'application/json',
  'Accept': '*/*'
}

def week_number():
    return datetime.date.today().isocalendar()[1]

def day_number():
    today = datetime.datetime.now()
    return (today - datetime.datetime(today.year, 1, 1)).days + 1

def get_event_data(event, user, chat):
    event_data = {
        'insert_id': str(uuid.uuid4()),
        'user_id': str(user.id),
        'device_id': str(chat.id),
        'event_type': event['type'],
        'app_version': '1.0',
        'platform': 'Telegram'
    }

    if not 'user_properties' in event:
        event_data['user_properties'] = {
            'is_bot': user.is_bot,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'language_code': user.language_code
        }
    else:
        event_data['user_properties'] = event['user_properties']

    if 'properties' in event:
        event_data['event_properties'] = event['properties']
    
    return event_data

def send_event(event, user, chat):
    event_data = get_event_data(event, user, chat)

    data = {
        'api_key': os.getenv('AMPLITUDE_API_KEY'),
        'events': [event_data]
    }

    requests.post('https://api.amplitude.com/2/httpapi',
                  json=data,
                  headers = headers)

def send_first_launch_event(user, chat):
    event = {
        'type': 'Launch first time',
        'user_properties': {
            'is_bot': user.is_bot,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'language_code': user.language_code,
            'cohort_day': day_number(),
            'cohort_week': week_number(),
            'cohort_year': datetime.date.today().year
        }
    }
    send_event(event, user, chat)

def send_start_event(user, chat):
    event = {
        'type': 'Start'
    }
    send_event(event, user, chat)

def send_message_event(user, chat, message_type, intent, text):
    event = {
        'type': 'Message',
        'properties': {
            'type': message_type,
            'intent': intent,
            'text': text
        }
    }

    send_event(event, user, chat)

def send_item_sent_event(user, chat, item):
    event = {
        'type': 'Item sent',
        'properties': {
            'item': item
        }
    }

    send_event(event, user, chat)
