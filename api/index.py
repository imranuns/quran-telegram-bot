import os
import requests
import json
from flask import Flask, request
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# --- Environment Variables ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY')
JSONBIN_BIN_ID = os.environ.get('JSONBIN_BIN_ID') 

# Debug environment variables (remove in production)
logger.info(f"Environment check - TOKEN: {'✅' if TOKEN else '❌'}")
logger.info(f"Environment check - ADMIN_ID: {'✅' if ADMIN_ID else '❌'}")
logger.info(f"Environment check - JSONBIN_API_KEY: {'✅' if JSONBIN_API_KEY else '❌'}")
logger.info(f"Environment check - JSONBIN_BIN_ID: {'✅' if JSONBIN_BIN_ID else '❌'}")

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
        "surah_prompt": "እባкዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)।\nአጠቃቀም: `/surah 2`",
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
}

# --- Improved Database Functions (JSONBin.io) ---
def test_jsonbin_connection():
    """Test JSONBin.io connection and return status"""
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        return False, "Missing API credentials"
    
    headers = {
        'X-Master-Key': JSONBIN_API_KEY,
        'X-Bin-Meta': 'false'
    }
    
    try:
        response = requests.get(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}',
            headers=headers,
            timeout=10
        )
        logger.info(f"JSONBin response status: {response.status_code}")
        logger.info(f"JSONBin response content: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            return True, f"Connection successful. Current data: {data}"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        logger.error(f"JSONBin connection test failed: {e}")
        return False, str(e)

def get_db():
    """Get database with improved error handling and logging"""
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        logger.error("Missing JSONBin credentials")
        return {'users': []}
    
    headers = {
        'X-Master-Key': JSONBIN_API_KEY,
        'X-Bin-Meta': 'false'
    }
    
    try:
        logger.info("Attempting to fetch data from JSONBin...")
        response = requests.get(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}',
            headers=headers,
            timeout=10
        )
        
        logger.info(f"JSONBin GET response: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully retrieved data: {data}")
        
        # Ensure the data has the expected structure
        if 'users' not in data:
            data = {'users': []}
            logger.info("Initialized empty users list")
            
        return data
        
    except requests.exceptions.Timeout:
        logger.error("JSONBin request timed out")
        return {'users': []}
    except requests.exceptions.RequestException as e:
        logger.error(f"JSONBin request failed: {e}")
        return {'users': []}
    except Exception as e:
        logger.error(f"Unexpected error getting DB: {e}")
        return {'users': []}

def update_db(data):
    """Update database with improved error handling and logging"""
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        logger.error("Missing JSONBin credentials for update")
        return False
    
    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': JSONBIN_API_KEY
    }
    
    try:
        logger.info(f"Attempting to update JSONBin with data: {data}")
        response = requests.put(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}',
            json=data,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"JSONBin PUT response: {response.status_code}")
        response.raise_for_status()
        
        logger.info("Successfully updated database")
        return True
        
    except requests.exceptions.Timeout:
        logger.error("JSONBin update request timed out")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"JSONBin update failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating DB: {e}")
        return False

def add_user_to_db(user_id):
    """Add user to database with improved logging"""
    try:
        logger.info(f"Adding user {user_id} to database...")
        db_data = get_db()
        users = db_data.get('users', [])
        
        if user_id not in users:
            users.append(user_id)
            db_data['users'] = users
            success = update_db(db_data)
            if success:
                logger.info(f"Successfully added user {user_id}. Total users: {len(users)}")
            else:
                logger.error(f"Failed to add user {user_id} to database")
        else:
            logger.info(f"User {user_id} already exists in database")
            
    except Exception as e:
        logger.error(f"Error in add_user_to_db: {e}")

# ቴሌግራም ላይ መልዕክት ለመላክ የሚረዳ ተግባር
def send_telegram_message(chat_id, text, parse_mode="Markdown", reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        logger.error("Telegram message send timeout")
    except Exception as e:
        logger.error(f"Error sending telegram message: {e}")

def get_user_lang(chat_id):
    return user_languages.get(chat_id, 'am')

def is_user_member(user_id):
    if not CHANNEL_ID: return True
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
        payload = {'chat_id': CHANNEL_ID, 'user_id': user_id}
        response = requests.get(url, params=payload, timeout=5)
        data = response.json()
        if data.get('ok'):
            status = data['result']['status']
            return status in ['creator', 'administrator', 'member']
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False
    return False

def handle_surah(chat_id, args, lang):
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114: raise ValueError
        response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}")
        data = response.json()['data']
        surah_name = data['englishName']
        ayahs = data['ayahs']
        message = f"🕋 *Surah {surah_number}: {surah_name}*\n\n"
        for ayah in ayahs:
            message += f"{ayah['numberInSurah']}. {ayah['text']}\n"
        for i in range(0, len(message), 4096):
            send_telegram_message(chat_id, message[i:i+4096])
    except (IndexError, ValueError):
        send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
    except Exception:
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(full_audio_url="N/A"))

def handle_juz(chat_id, args, lang):
    try:
        juz_number = int(args[0])
        if not 1 <= juz_number <= 30: raise ValueError
        response = requests.get(f"{QURAN_API_BASE_URL}/juz/{juz_number}")
        data = response.json()['data']
        ayahs = data['ayahs']
        message = f"📗 *Juz' {juz_number}*\n\n"
        current_surah_name = ""
        for ayah in ayahs:
            if ayah['surah']['name'] != current_surah_name:
                current_surah_name = ayah['surah']['name']
                message += f"\n--- {current_surah_name} ---\n"
            message += f"{ayah['numberInSurah']}. {ayah['text']}\n"
        for i in range(0, len(message), 4096):
            send_telegram_message(chat_id, message[i:i+4096])
    except (IndexError, ValueError):
        send_telegram_message(chat_id, MESSAGES[lang]["juz_prompt"])
    except Exception:
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(full_audio_url="N/A"))

def handle_recitation(chat_id, args, lang, reciter_key):
    full_audio_url = ""
    try:
        if not args:
            send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
            return
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114: raise ValueError
        reciter_info = RECITERS[reciter_key]
        reciter_name = reciter_info['name']
        reciter_identifier = reciter_info['identifier']
        surah_info_response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}")
        surah_data = surah_info_response.json()['data']
        surah_name_english = surah_data['englishName']
        padded_surah_number = str(surah_number).zfill(3)
        full_audio_url = f"https://download.quranicaudio.com/quran/{reciter_identifier}/{padded_surah_number}.mp3"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(full_audio_url, headers=headers, stream=True, timeout=15)
        if response.status_code != 200:
            raise Exception(f"File not found, status code: {response.status_code}")
        message_text = MESSAGES[lang]["audio_link_message"].format(audio_url=full_audio_url)
        send_telegram_message(chat_id, message_text)
    except (IndexError, ValueError):
        send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
    except Exception as e:
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(full_audio_url=full_audio_url))

# --- Improved Admin Commands ---
def handle_status(chat_id):
    """Handle status command with detailed debugging info"""
    try:
        # Test connection first
        is_connected, connection_info = test_jsonbin_connection()
        
        db_data = get_db()
        user_count = len(db_data.get('users', []))
        
        status_message = f"📊 *Bot Status*\n\n"
        status_message += f"Total Users: *{user_count}*\n\n"
        status_message += f"🔗 JSONBin Connection: {'✅' if is_connected else '❌'}\n"
        
        if str(chat_id) == ADMIN_ID:
            # Show detailed debug info to admin
            status_message += f"\n*Debug Info:*\n"
            status_message += f"API Key: {'✅' if JSONBIN_API_KEY else '❌'}\n"
            status_message += f"Bin ID: {'✅' if JSONBIN_BIN_ID else '❌'}\n"
            status_message += f"Connection: {connection_info[:200]}\n"
        
        send_telegram_message(chat_id, status_message)
        
    except Exception as e:
        logger.error(f"Error in handle_status: {e}")
        send_telegram_message(chat_id, f"❌ Error getting status: {str(e)}")

def handle_broadcast(admin_id, message_text):
    """Handle broadcast with improved error reporting"""
    try:
        db_data = get_db()
        users = db_data.get('users', [])
        
        if not users:
            send_telegram_message(admin_id, "❌ No users found in database. Check your JSONBin connection.")
            return
        
        sent_count = 0
        failed_count = 0
        
        for user_id in users:
            try:
                send_telegram_message(user_id, message_text)
                sent_count += 1
                time.sleep(0.1)
            except Exception as e:
                failed_count += 1
                logger.error(f"Could not broadcast to {user_id}: {e}")
        
        result_message = f"✅ Broadcast completed!\n\n"
        result_message += f"📤 Sent to: *{sent_count}* users\n"
        result_message += f"❌ Failed: *{failed_count}* users\n"
        result_message += f"📊 Total in DB: *{len(users)}* users"
        
        send_telegram_message(admin_id, result_message)
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast: {e}")
        send_telegram_message(admin_id, f"❌ Broadcast failed: {str(e)}")

# Add debug command for admin
def handle_debug(chat_id):
    """Debug command to test database operations"""
    if str(chat_id) != ADMIN_ID:
        return
    
    try:
        # Test connection
        is_connected, connection_info = test_jsonbin_connection()
        
        debug_message = f"🔧 *Debug Information*\n\n"
        debug_message += f"JSONBin Connection: {'✅' if is_connected else '❌'}\n"
        debug_message += f"Connection Info: {connection_info[:300]}\n\n"
        
        # Test database operations
        db_data = get_db()
        debug_message += f"Current DB Data: {db_data}\n\n"
        
        # Test adding a user
        test_user_id = 999999999  # Test user ID
        add_user_to_db(test_user_id)
        
        # Check if it was added
        updated_data = get_db()
        debug_message += f"After test user addition: {updated_data}\n"
        
        send_telegram_message(chat_id, debug_message)
        
    except Exception as e:
        logger.error(f"Error in debug command: {e}")
        send_telegram_message(chat_id, f"❌ Debug error: {str(e)}")

# ዋናው መግቢያ (Webhook)
@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if 'callback_query' in update:
        callback_query = update['callback_query']
        data = callback_query['data']
        chat_id = callback_query['message']['chat']['id']
        if data.startswith('set_lang_'):
            lang_code = data.split('_')[-1]
            user_languages[chat_id] = lang_code
            lang = get_user_lang(chat_id)
            send_telegram_message(chat_id, MESSAGES[lang]["language_selected"])
        return 'ok'

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

        add_user_to_db(user_id)

        is_admin = str(user_id) == ADMIN_ID
        
        if not is_admin and not is_user_member(user_id):
            channel_name = CHANNEL_ID.replace('@', '') if CHANNEL_ID else ''
            keyboard = {"inline_keyboard": [[{"text": MESSAGES[lang]["join_button_text"], "url": f"https://t.me/{channel_name}"}]]}
            send_telegram_message(chat_id, MESSAGES[lang]["force_join"], reply_markup=keyboard)
            return 'ok'

        if command == '/start':
            send_telegram_message(chat_id, MESSAGES[lang]["welcome"].format(username=user_name))
        elif command == '/language':
            keyboard = {"inline_keyboard": [[{"text": "አማርኛ", "callback_data": "set_lang_am"}, {"text": "English", "callback_data": "set_lang_en"}],[{"text": "العربية", "callback_data": "set_lang_ar"}, {"text": "Türkçe", "callback_data": "set_lang_tr"}]]}
            send_telegram_message(chat_id, MESSAGES[lang]["language_prompt"], reply_markup=keyboard)
        elif command == '/support':
            if not args:
                send_telegram_message(chat_id, MESSAGES[lang]["support_prompt"])
            else:
                support_message = " ".join(args)
                forward_message = f"🆘 *New Support Message*\n\n*From:* {user_name} (ID: `{user_id}`)\n\n*Message:* {support_message}"
                if ADMIN_ID: send_telegram_message(ADMIN_ID, forward_message)
                send_telegram_message(chat_id, MESSAGES[lang]["support_sent"])
        elif is_admin and command == '/status':
            handle_status(chat_id)
        elif is_admin and command == '/broadcast':
            if not args:
                send_telegram_message(chat_id, "Please provide a message to broadcast.\nUsage: `/broadcast Hello everyone!`")
            else:
                broadcast_text = " ".join(args)
                handle_broadcast(chat_id, broadcast_text)
        elif is_admin and command == '/debug':
            handle_debug(chat_id)
        elif command == '/surah': handle_surah(chat_id, args, lang)
        elif command == '/juz': handle_juz(chat_id, args, lang)
        else:
            reciter_command = command.replace('/', '')
            if reciter_command in RECITERS:
                handle_recitation(chat_id, args, lang, reciter_command)
    return 'ok'

@app.route('/')
def index():
    return "Bot is running with admin features!"

@app.route('/test')
def test():
    """Test endpoint to verify deployment and database connectivity"""
    try:
        # Test environment variables
        env_status = {
            'TELEGRAM_TOKEN': '✅' if TOKEN else '❌',
            'ADMIN_ID': '✅' if ADMIN_ID else '❌',
            'JSONBIN_API_KEY': '✅' if JSONBIN_API_KEY else '❌',
            'JSONBIN_BIN_ID': '✅' if JSONBIN_BIN_ID else '❌'
        }
        
        # Test JSONBin connection
        is_connected, connection_info = test_jsonbin_connection()
        
        # Test database read
        db_data = get_db()
        user_count = len(db_data.get('users', []))
        
        result = {
            'status': 'OK',
            'timestamp': datetime.now().isoformat(),
            'environment_variables': env_status,
            'jsonbin_connection': {
                'connected': is_connected,
                'info': connection_info
            },
            'database': {
                'user_count': user_count,
                'data': db_data
            }
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, indent=2)
