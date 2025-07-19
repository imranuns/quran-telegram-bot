import os
import requests
import json
from flask import Flask, request
import time

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# --- Environment Variables ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
# *** አዲስ: ከ JSONBin.io ያገኙትን Master Key እዚህ ያስገቡ (Vercel ላይ) ***
JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY')
# *** አዲስ: ለዳታቤዝ የምንጠቀምበት የ Bin ID (በመጀመሪያው ሩጫ ይፈጠራል) ***
JSONBIN_BIN_ID = os.environ.get('JSONBIN_BIN_ID') 

QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'

# የቃሪዎች ዝርዝር
RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 'abdul_basit_murattal'},
    'yasser': {'name': 'Yasser Al-Dosari', 'identifier': 'yasser_ad-dussary'},
}

# የተጠቃሚ ቋንቋ ምርጫን ለማስቀመጥ
user_languages = {}

# የቦቱ መልዕክቶች በአራት ቋንቋ
MESSAGES = {
    'am': {
        "welcome": "🕌 Assalamu Alaikum {username}\n\n📖 ወደ ቁርአን ቦት በደህና መጡ!\n\n✍️ ለጽሁፍ የቁርአን አንቀጾች:\n\n/surah <ቁጥር> — ሱራ ቁጥር አስገባ\n/juz <ቁጥር> — ጁዝ ቁጥር አስገባ\n\n🔊 ለድምጽ (ሙሉ ሱራ ኮርኖች):\n/abdulbasit <ቁጥር> 🎙️\n/yasser <ቁጥር> 🎧\n\n⚙️ ሌሎች ትዕዛዞች:\n🌐 /language — ቋንቋ ለመቀየር\n🆘 /support <መልዕክት> — ለእርዳታ ለአድሚኑ ይላኩ",
        "language_prompt": "እባክዎ ቋንቋ ይምረጡ:",
        "language_selected": "✅ ቋንቋ ወደ አማርኛ ተቀይሯል።",
        "support_prompt": "እባክዎ ከ `/support` ትዕዛዝ በኋላ መልዕክትዎን ያስገቡ።\nምሳሌ: `/support ሰላም፣ እርዳታ እፈልጋለሁ`",
        "support_sent": "✅ መልዕክትዎ ለአድሚኑ ተልኳል።",
        "force_join": "🙏 ቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
        "join_button_text": "✅ please first join channel",
        "surah_prompt": "እባкዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/surah 2`",
        "juz_prompt": "እባкዎ ትክክለኛ የጁዝ ቁጥር ያስገቡ (1-30)።\nአጠቃቀም: `/juz 15`",
        "audio_link_message": "🔗 [Download / Play Audio Here]({audio_url})\n\nከላይ ያለውን ሰማያዊ ሊንክ በመጫን ድምጹን በቀጥታ ማዳመጥ ወይም ማውረድ ይችላሉ።",
        "error_fetching": "ይቅርታ፣ የድምጽ ፋይሉን ሊንክ ማግኘት አልቻልኩም።\n\n**ምክንያት:** የድምጽ ፋይሉ በድረ-ገጹ ላይ አልተገኘም (404 Error)።\n**የተሞከረው ሊንክ:** `{full_audio_url}`"
    },
    'en': {
        "welcome": "🕌 Assalamu Alaikum {username}\n\n📖 Welcome to the Quran Bot!\n\n✍️ For Quran verses in text:\n\n/surah <number> — Enter Surah number\n/juz <number> — Enter Juz' number\n\n🔊 For Audio (Full Surah Recitations):\n/abdulbasit <number> 🎙️\n/yasser <number> 🎧\n\n⚙️ Other Commands:\n🌐 /language — To change language\n🆘 /support <message> — Send a message to the admin for help",
        "language_prompt": "Please select a language:",
        "language_selected": "✅ Language changed to English.",
        "support_prompt": "Please enter your message after the `/support` command.\nExample: `/support Hello, I need help`",
        "support_sent": "✅ Your message has been sent to the admin.",
        "force_join": "🙏 To use the bot, please join our channel first.",
        "join_button_text": "✅ please first join channel",
        "surah_prompt": "Please provide a valid Surah number (1-114).\nUsage: `/surah 2`",
        "juz_prompt": "Please provide a valid Juz' number (1-30).\nUsage: `/juz 15`",
        "audio_link_message": "🔗 [Download / Play Audio Here]({audio_url})\n\nYou can listen or download the audio by clicking the blue link above.",
        "error_fetching": "Sorry, I could not get the audio link.\n\n**Reason:** The audio file was not found on the server (404 Error).\n**Attempted Link:** `{full_audio_url}`"
    }
    # (For brevity, Arabic and Turkish translations are omitted but would follow the same structure)
}

# --- Database Functions (JSONBin.io) ---
def get_db():
    headers = {'X-Master-Key': JSONBIN_API_KEY}
    try:
        req = requests.get(f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest', headers=headers)
        req.raise_for_status()
        return req.json()['record']
    except Exception as e:
        print(f"Error getting DB: {e}")
        return {'users': []} # Return empty structure on error

def update_db(data):
    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': JSONBIN_API_KEY
    }
    try:
        req = requests.put(f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}', json=data, headers=headers)
        req.raise_for_status()
    except Exception as e:
        print(f"Error updating DB: {e}")

def add_user_to_db(user_id):
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        return
    db_data = get_db()
    if user_id not in db_data.get('users', []):
        db_data['users'].append(user_id)
        update_db(db_data)

# ቴሌግራም ላይ መልዕክት ለመላክ የሚረዳ ተግባር
def send_telegram_message(chat_id, text, parse_mode="Markdown", reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.Timeout:
        pass

def get_user_lang(chat_id):
    return user_languages.get(chat_id, 'am')

# ተጠቃሚው ቻናሉን መቀላቀሉን የሚያረጋግጥ ተግባር
def is_user_member(user_id):
    if not CHANNEL_ID:
        return True
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
        payload = {'chat_id': CHANNEL_ID, 'user_id': user_id}
        response = requests.get(url, params=payload)
        data = response.json()
        if data.get('ok'):
            status = data['result']['status']
            return status in ['creator', 'administrator', 'member']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False
    return False

# ሱራ እና ጁዝ ተግባራት (ከበፊቱ ጋር ተመሳሳይ)
def handle_surah(chat_id, args, lang):
    # (Code from previous version)
    pass
def handle_juz(chat_id, args, lang):
    # (Code from previous version)
    pass
def handle_recitation(chat_id, args, lang, reciter_key):
    # (Code from previous version)
    pass

# --- Admin Commands ---
def handle_status(chat_id):
    db_data = get_db()
    user_count = len(db_data.get('users', []))
    send_telegram_message(chat_id, f"📊 *Bot Status*\n\nTotal Users: *{user_count}*")

def handle_broadcast(admin_id, message_text):
    db_data = get_db()
    users = db_data.get('users', [])
    sent_count = 0
    for user_id in users:
        try:
            send_telegram_message(user_id, message_text)
            sent_count += 1
            time.sleep(0.1) # Avoid hitting rate limits
        except Exception as e:
            print(f"Could not broadcast to {user_id}: {e}")
    send_telegram_message(admin_id, f"✅ Broadcast sent to *{sent_count}* out of *{len(users)}* users.")


# ዋናው መግቢያ (Webhook)
@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()
    
    # Callback Query
    if 'callback_query' in update:
        # (Code from previous version)
        pass

    # Normal Message
    if 'message' in update:
        message = update['message']
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        user_name = message['from'].get('first_name', 'User')
        text = message.get('text', '')
        command_parts = text.split()
        command = command_parts[0].lower()
        args = command_parts[1:]
        lang = get_user_lang(chat_id)

        # Add user to DB
        add_user_to_db(user_id)

        # የቻናል አባልነት ማረጋገጫ
        is_admin = str(user_id) == ADMIN_ID
        
        if not is_admin and not is_user_member(user_id):
            # (Code from previous version)
            return 'ok'

        # --- Command Handling ---
        if command == '/start':
            send_telegram_message(chat_id, MESSAGES[lang]["welcome"].format(username=user_name))

        elif command == '/language':
            # (Code from previous version)
            pass
        
        elif command == '/support':
            if not args:
                send_telegram_message(chat_id, MESSAGES[lang]["support_prompt"])
            else:
                support_message = " ".join(args)
                forward_message = f"🆘 *New Support Message*\n\n*From:* {user_name} (ID: `{user_id}`)\n\n*Message:* {support_message}"
                send_telegram_message(ADMIN_ID, forward_message)
                send_telegram_message(chat_id, MESSAGES[lang]["support_sent"])

        # --- Admin-Only Commands ---
        elif is_admin and command == '/status':
            handle_status(chat_id)

        elif is_admin and command == '/broadcast':
            if not args:
                send_telegram_message(chat_id, "Please provide a message to broadcast.\nUsage: `/broadcast Hello everyone!`")
            else:
                broadcast_text = " ".join(args)
                handle_broadcast(chat_id, broadcast_text)

        elif command == '/surah': handle_surah(chat_id, args, lang)
        elif command == '/juz': handle_juz(chat_id, args, lang)
        
        reciter_command = command.replace('/', '')
        if reciter_command in RECITERS:
            handle_recitation(chat_id, args, lang, reciter_command)

    return 'ok'

@app.route('/')
def index():
    return "Bot is running with admin features!"
