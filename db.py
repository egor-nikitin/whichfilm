import pyrebase
import os
import analytics
import time

def init(ctx):
    config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': 'whichfilmbot.firebaseapp.com',
        'databaseURL': 'https://whichfilmbot.firebaseio.com',
        'projectId': 'whichfilmbot',
        'storageBucket': 'whichfilmbot.appspot.com',
        'messagingSenderId': '914533040757',
        'appId': '1:914533040757:web:6410e7bf9f046353cc2e3c'
    }

    firebase = pyrebase.initialize_app(config)

    ctx['auth'] = firebase.auth()
    ctx['db_auth_updated_at'] = 0
    ctx['db_user'] = {}
    ctx['db'] = firebase.database()
    ctx['firebase'] = firebase

def refresh_auth(ctx):
    if ctx['db_auth_updated_at'] == 0:
        ctx['db_user'] = ctx['auth'].sign_in_with_email_and_password('yegor.nikitin@gmail.com', os.getenv("FIREBASE_PASSWORD"))
        ctx['db_auth_updated_at'] = time.time()
    elif (time.time() - ctx['db_auth_updated_at'] > 3500):
        ctx['db_user'] = ctx['auth'].refresh(ctx['db_user']['refreshToken'])
        ctx['db_auth_updated_at'] = time.time()

def update_items_cache(ctx):
    if ctx['items'] == []:
        db_items = ctx['db'].child(ctx['db_user']['localId']).child("items").get(ctx['db_user']['idToken'])
        for db_item in db_items.each():
            item = db_item.val()
            item['id'] = db_item.key()
            ctx['items'].append(item)

def update_item(ctx, item):
    ctx['db'].child(ctx['db_user']['localId']).child("items").child(item['id']).update(item, ctx['db_user']['idToken'])

def save_user(ctx, user, chat):
    user_db = ctx['db'].child(ctx['db_user']['localId']).child("users").child(user.id).get(ctx['db_user']['idToken'])
    if not user_db.val():
        user_data = {
            'id': user.id,
            'is_bot': user.is_bot,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'language_code': user.language_code,
            'created_at': int(time.time())
        }
        ctx['db'].child(ctx['db_user']['localId']).child("users").child(user.id).set(user_data, ctx['db_user']['idToken'])        
        return True
    return False
