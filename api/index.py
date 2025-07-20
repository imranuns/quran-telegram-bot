import os
import requests
import json
from flask import Flask, request
import time

app = Flask(__name__)

# --- Environment Variables ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY')
JSONBIN_BIN_ID = os.environ.get('JSONBIN_BIN_ID') 

QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'

RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 'abdul_basit_murattal'},
    'yasser': {'name': 'Yasser Al-Dosari', 'identifier': 'yasser_ad-dussary'},
}

user_languages = {}

MESSAGES = {
    'am': {
        "welcome": "🕌 Assalamu Alaikum {username}\n\n📖 ወደ ቁርአን ቦት በደህና መጡ!\n\n✍️ ለጽሁፍ የቁርአን አንቀጾች:\n\n/surah <ቁጥር> — ሱራ ቁጥር አስገባ\n/juz <ቁጥር> — ጁዝ ቁጥር አስገባ\n\n🔊 ለድምጽ (ሙሉ ሱራ ኮርኖች):\n/abdulbasit <ቁጥር> 🎙️\n/yasser <ቁጥር> 🎧\n\n⚙️ ሌሎች ትዕዛዞች:\n🌐 /language — ቋንቋ ለመቀየር\n🆘 /support <መልዕክት> — ለእርዳታ ለአድሚኑ ይላኩ",
        "support_prompt": "እባክዎ ከ `/support` ትዕዛዝ በኋላ መልዕክትዎን ያስገቡ።\nምሳሌ: `/support ሰላም፣ እርዳታ እፈልጋለሁ`",
        "support_sent": "✅ መልዕክትዎ ለአድሚኑ ተልኳል።",
        "force_join": "🙏 ቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
        "join_button_text": "✅ please first join channel",
    },
}

# --- Database Functions (JSONBin.io) ---
def get_db():
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        raise Exception("JSONBin API Key or Bin ID is missing.")
    headers = {'X-Master-Key': JSONBIN_API_KEY, 'X-Bin-Meta': 'false'}
    req = requests.get(f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}', headers=headers)
    req.raise_for_status()
    return req.json()

def update_db(data):
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        raise Exception("JSONBin API Key or Bin ID is missing.")
    headers = {'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_API_KEY}
    req = requests.put(f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}', json=data, headers=headers)
    req.raise_for_status()

def add_user_to_db(user_id):
    try:
        db_data = get_db()
        users = db_data.get('users', [])
        if user_id not in users:
            users.append(user_id)
            db_data['users'] = users
            update_db(db_data)
    except Exception as e:
        print(f"Error adding user to DB: {e}")


# --- Telegram Functions ---
def send_telegram_message(chat_id, text, parse_mode="Markdown", reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    requests.post(url, json=payload, timeout=5)

# --- Admin Commands ---
def handle_status(chat_id):
    try:
        db_data = get_db()
        user_count = len(db_data.get('users', []))
        send_telegram_message(chat_id, f"📊 *Bot Status*\n\nTotal Users: *{user_count}*")
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Could not get status. DB Error: `{e}`")

def handle_broadcast(admin_id, message_text):
    try:
        db_data = get_db()
        users = db_data.get('users', [])
        sent_count = 0
        for user_id in users:
            try:
                send_telegram_message(user_id, message_text)
                sent_count += 1
                time.sleep(0.1)
            except Exception:
                pass
        send_telegram_message(admin_id, f"✅ Broadcast sent to *{sent_count}* of *{len(users)}* users.")
    except Exception as e:
        send_telegram_message(admin_id, f"❌ Broadcast failed. DB Error: `{e}`")

# *** አዲሱ የዲበግ ትዕዛዝ ***
def handle_debug(chat_id):
    report = "*🐞 Debug Report*\n\n"
    report += "*Environment Variables:*\n"
    report += f"- `ADMIN_ID`: {'✅ Set' if ADMIN_ID else '❌ NOT SET'}\n"
    report += f"- `CHANNEL_ID`: {'✅ Set' if CHANNEL_ID else '❌ NOT SET'}\n"
    report += f"- `JSONBIN_API_KEY`: {'✅ Set' if JSONBIN_API_KEY else '❌ NOT SET'}\n"
    report += f"- `JSONBIN_BIN_ID`: {'✅ Set' if JSONBIN_BIN_ID else '❌ NOT SET'}\n\n"
    
    report += "*JSONBin.io Connection Test:*\n"
    try:
        get_db()
        report += "✅ Connection Successful!\n"
    except Exception as e:
        report += f"❌ Connection Failed!\n   *Error:* `{e}`"
        
    send_telegram_message(chat_id, report)


# --- Webhook Handler ---
@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'message' in update:
        message = update['message']
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        user_name = message['from'].get('first_name', 'User')
        text = message.get('text', '')
        command_parts = text.split()
        command = command_parts[0].lower()
        args = command_parts[1:]
        
        add_user_to_db(user_id)
        is_admin = str(user_id) == ADMIN_ID
        
        if command == '/start':
            send_telegram_message(chat_id, MESSAGES['am']["welcome"].format(username=user_name))
        
        # --- Admin-Only Commands ---
        elif is_admin and command == '/status':
            handle_status(chat_id)
        elif is_admin and command == '/broadcast':
            if not args:
                send_telegram_message(chat_id, "Usage: `/broadcast <message>`")
            else:
                handle_broadcast(chat_id, " ".join(args))
        elif is_admin and command == '/debug':
            handle_debug(chat_id)

    return 'ok'

@app.route('/')
def index():
    return "Bot is running with debug features!"
