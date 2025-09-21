import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth

cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Replace with your test user's UID or email
user = auth.get_user_by_email('test@amikiyo.com')
token = auth.create_custom_token(user.uid)
print(token.decode('utf-8'))