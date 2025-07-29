import os
import requests
import json
import logging
import time
from flask import Flask, request

# --- Basic Configuration ---
# Set up logging to see detailed output in your Vercel logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Environment Variables ---
# It's crucial that these are all set correctly in your Vercel project settings.
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY')
JSONBIN_BIN_ID = os.environ.get('JSONBIN_BIN_ID')

# --- Constants ---
QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'
RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 'abdul_basit_murattal'},
    'yasser': {'name': 'Yasser Al-Dosari', 'identifier': 'yasser_ad-dussary'},
}

# --- All Bot Text in One Place ---
# This makes it easy to manage and add new languages in the future.
MESSAGES = {
    'am': {
        "welcome": "🕌 Assalamu Alaikum {username}\n\n📖 ወደ ቁርአን ቦት በደህና መጡ!\n\n✍️ ለጽሁፍ የቁርአን አንቀጾች:\n\n/surah <ቁጥር> — ሱራ ቁጥር አስገባ\n/juz <ቁጥር> — ጁዝ ቁጥር አስገባ\n\n🔊 ለድምጽ (ሙሉ ሱራ ኮርኖች):\n/abdulbasit <ቁጥር> 🎙️\n/yasser <ቁጥር> 🎧\n\n⚙️ ሌሎች ትዕዛዞች:\n🌐 /language — ቋንቋ ለመቀየር\n🆘 /support <መልዕክት> — ለእርዳታ ለአድሚኑ ይላኩ",
        "language_prompt": "እባክዎ ቋንቋ ይምረጡ:",
        "language_selected": "✅ ቋንቋ ወደ አማርኛ ተቀይሯል።",
        "support_prompt": "እባክዎ ከ `/support` ትዕዛዝ በኋላ መልዕክትዎን ያስገቡ።\nምሳሌ: `/support ሰላም፣ እርዳታ እፈልጋለሁ`",
        "support_sent": "✅ መልዕክትዎ ለአድሚኑ ተልኳል።",
        "force_join": "🙏 ቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
        "join_button_text": "✅ ቻናሉን ይቀላቀሉ",
        "surah_prompt": "እባክዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/surah 2`",
        "juz_prompt": "እባክዎ ትክክለኛ የጁዝ ቁጥር ያስገቡ (1-30)።\nአጠቃቀም: `/juz 15`",
        "reciter_prompt": "እባክዎ ከቃሪኡ ስም ቀጥሎ የሱራውን ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/{reciter_key} 2`",
        "audio_link_message": "🎧 *{reciter_name}*\n📖 *Surah {surah_name}*\n\n🔗 [Download / Play Audio Here]({audio_url})\n\nከላይ ያለውን ሰማያዊ ሊንክ በመጫን ድምጹን በቀጥታ ማዳመጥ ወይም ማውረድ ይችላሉ።",
        "error_fetching_audio": "ይቅርታ፣ የድምጽ ፋይሉን ሊንክ ማግኘት አልቻልኩም።\n\n**ምክንያት:** የድምጽ ፋይሉ በድረ-ገጹ ላይ አልተገኘም (404 Error)።\n**የተሞከረው ሊንክ:** `{full_audio_url}`",
        "generic_error": "❌ አንድ ስህተት አጋጥሟል። እባክዎ ቆይተው እንደገና ይሞክሩ። ችግሩ ከቀጠለ ለአስተዳዳሪው ያሳውቁ።"
    },
    'en': {
        "welcome": "🕌 Assalamu Alaikum {username}\n\n📖 Welcome to the Quran Bot!\n\n✍️ For Quran verses in text:\n\n/surah <number> — Enter Surah number\n/juz <number> — Enter Juz' number\n\n🔊 For Audio (Full Surah Recitations):\n/abdulbasit <number> 🎙️\n/yasser <number> 🎧\n\n⚙️ Other Commands:\n🌐 /language — To change language\n🆘 /support <message> — Send a message to the admin for help",
        "language_prompt": "Please select a language:",
        "language_selected": "✅ Language changed to English.",
        "support_prompt": "Please enter your message after the `/support` command.\nExample: `/support Hello, I need help`",
        "support_sent": "✅ Your message has been sent to the admin.",
        "force_join": "🙏 To use the bot, please join our channel first.",
        "join_button_text": "✅ Join Channel",
        "surah_prompt": "Please provide a valid Surah number (1-114).\nUsage: `/surah 2`",
        "juz_prompt": "Please provide a valid Juz' number (1-30).\nUsage: `/juz 15`",
        "reciter_prompt": "Please enter the Surah number after the reciter's name (1-114).\nUsage: `/{reciter_key} 2`",
        "audio_link_message": "🎧 *{reciter_name}*\n📖 *Surah {surah_name}*\n\n🔗 [Download / Play Audio Here]({audio_url})\n\nYou can listen or download the audio by clicking the blue link above.",
        "error_fetching_audio": "Sorry, I could not get the audio link.\n\n**Reason:** The audio file was not found on the server (404 Error).\n**Attempted Link:** `{full_audio_url}`",
        "generic_error": "❌ An error occurred. Please try again later. If the problem persists, contact the admin."
    },
    # ... other languages (ar, tr) go here, similar structure ...
}


# --- Database Functions (JSONBin.io) ---
# These functions now handle a more structured database.
# DB Structure: {"users": {"user_id_1": {"lang": "en"}, "user_id_2": {"lang": "am"}}}

def get_db():
    """Fetches the entire database from JSONBin.io."""
    if not all([JSONBIN_BIN_ID, JSONBIN_API_KEY]):
        logging.error("JSONBin API Key or Bin ID is missing.")
        raise ValueError("JSONBin configuration is incomplete.")
    headers = {'X-Master-Key': JSONBIN_API_KEY, 'X-Bin-Meta': 'false'}
    try:
        req = requests.get(f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}', headers=headers, timeout=10)
        req.raise_for_status()
        return req.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get DB from JSONBin: {e}")
        raise

def update_db(data):
    """Updates the entire database on JSONBin.io."""
    if not all([JSONBIN_BIN_ID, JSONBIN_API_KEY]):
        logging.error("JSONBin API Key or Bin ID is missing.")
        raise ValueError("JSONBin configuration is incomplete.")
    headers = {'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_API_KEY}
    try:
        req = requests.put(f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}', json=data, headers=headers, timeout=10)
        req.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to update DB on JSONBin: {e}")
        raise

def get_user_data(user_id):
    """Gets specific user's data from the DB, or returns a default."""
    try:
        db_data = get_db()
        return db_data.get('users', {}).get(str(user_id), {'lang': 'am'}) # Default to Amharic
    except Exception:
        # If DB fails, return a temporary default to keep the bot responsive
        return {'lang': 'am'}

def set_user_lang(user_id, lang_code):
    """Adds a user or updates their language in the database."""
    try:
        db_data = get_db()
        if 'users' not in db_data:
            db_data['users'] = {}
        # Ensure user_id is a string, as JSON keys must be strings
        db_data['users'][str(user_id)] = {'lang': lang_code}
        update_db(db_data)
        logging.info(f"Set language for user {user_id} to {lang_code}")
    except Exception as e:
        logging.error(f"Failed to set language for user {user_id}: {e}")


# --- Telegram API Functions ---
def send_telegram_message(chat_id, text, parse_mode="Markdown", reply_markup=None):
    """Sends a message via the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Message sent to chat_id: {chat_id}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to {chat_id}: {e}")

def is_user_member(user_id):
    """Checks if a user is a member of the specified channel. No caching."""
    if not CHANNEL_ID:
        logging.warning("CHANNEL_ID is not set. Skipping membership check.")
        return True
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
        payload = {'chat_id': CHANNEL_ID, 'user_id': user_id}
        response = requests.get(url, params=payload, timeout=5)
        response.raise_for_status()
        status = response.json().get('result', {}).get('status')
        logging.info(f"User {user_id} membership status in {CHANNEL_ID} is: {status}")
        return status in ['creator', 'administrator', 'member']
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not check membership for user {user_id}: {e}")
        # Fail-safe: If the check fails, deny access to prevent bypassing the join requirement.
        return False


# --- Bot Feature Functions ---
def handle_surah(chat_id, args, lang):
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114:
            raise ValueError("Invalid Surah number")
        
        response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}", timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        
        surah_name = data['englishName']
        ayahs = data['ayahs']
        message = f"🕋 *Surah {surah_number}: {surah_name}*\n\n"
        for ayah in ayahs:
            message += f"{ayah['numberInSurah']}. {ayah['text']}\n"
        
        # Telegram has a message length limit of 4096 characters
        for i in range(0, len(message), 4096):
            send_telegram_message(chat_id, message[i:i+4096])
            
    except (ValueError, IndexError):
        send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
    except requests.exceptions.RequestException as e:
        logging.error(f"API error fetching surah {args[0]}: {e}")
        send_telegram_message(chat_id, MESSAGES[lang]["generic_error"])
    except KeyError:
        logging.error(f"API response for surah {args[0]} had unexpected structure.")
        send_telegram_message(chat_id, MESSAGES[lang]["generic_error"])


def handle_recitation(chat_id, args, lang, reciter_key):
    full_audio_url = ""
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114:
            raise ValueError("Invalid Surah number")

        reciter_info = RECITERS[reciter_key]
        padded_surah_number = str(surah_number).zfill(3)
        full_audio_url = f"https://download.quranicaudio.com/quran/{reciter_info['identifier']}/{padded_surah_number}.mp3"

        # First get Surah name for the message
        surah_info_response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}", timeout=10)
        surah_info_response.raise_for_status()
        surah_name_english = surah_info_response.json()['data']['englishName']

        # Check if the audio file actually exists before sending the link
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(full_audio_url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code != 200:
            logging.warning(f"Audio file not found (HTTP {response.status_code}) at {full_audio_url}")
            send_telegram_message(chat_id, MESSAGES[lang]["error_fetching_audio"].format(full_audio_url=full_audio_url))
            return

        message_text = MESSAGES[lang]["audio_link_message"].format(
            reciter_name=reciter_info['name'],
            surah_name=surah_name_english,
            audio_url=full_audio_url
        )
        send_telegram_message(chat_id, message_text)

    except (ValueError, IndexError):
        send_telegram_message(chat_id, MESSAGES[lang]["reciter_prompt"].format(reciter_key=reciter_key))
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching recitation for surah {args[0]}: {e}")
        send_telegram_message(chat_id, MESSAGES[lang]["generic_error"])
    except KeyError:
        logging.error(f"API response for recitation surah {args[0]} had unexpected structure.")
        send_telegram_message(chat_id, MESSAGES[lang]["generic_error"])


# --- Webhook Handler ---
@app.route('/', methods=['POST'])
def webhook():
    try:
        update = request.get_json()

        if 'callback_query' in update:
            callback_data = update['callback_query']['data']
            chat_id = update['callback_query']['message']['chat']['id']
            user_id = update['callback_query']['from']['id']

            if callback_data.startswith('set_lang_'):
                lang_code = callback_data.split('_')[-1]
                set_user_lang(user_id, lang_code)
                send_telegram_message(chat_id, MESSAGES[lang_code]["language_selected"])
            return 'ok', 200

        if 'message' in update:
            message = update['message']
            user_id = message['from']['id']
            chat_id = message['chat']['id']
            user_name = message['from'].get('first_name', 'User')
            text = message.get('text', '')

            if not text.startswith('/'):
                return 'ok', 200 # Ignore non-command messages

            # Get user language from DB
            user_data = get_user_data(user_id)
            lang = user_data.get('lang', 'am')

            # --- Force Join Check ---
            is_admin = str(user_id) == ADMIN_ID
            if not is_admin and not is_user_member(user_id):
                channel_name = CHANNEL_ID.replace('@', '') if CHANNEL_ID else ''
                if channel_name:
                    keyboard = {"inline_keyboard": [[{"text": MESSAGES[lang]["join_button_text"], "url": f"https://t.me/{channel_name}"}]]}
                    send_telegram_message(chat_id, MESSAGES[lang]["force_join"], reply_markup=keyboard)
                else:
                    send_telegram_message(chat_id, MESSAGES[lang]["force_join"])
                return 'ok', 200

            # --- Command Handling ---
            command_parts = text.split()
            command = command_parts[0].lower()
            args = command_parts[1:]

            if command == '/start':
                set_user_lang(user_id, lang) # Add user to DB on start
                send_telegram_message(chat_id, MESSAGES[lang]["welcome"].format(username=user_name))
            
            elif command == '/language':
                keyboard = {"inline_keyboard": [
                    [{"text": "አማርኛ", "callback_data": "set_lang_am"}, {"text": "English", "callback_data": "set_lang_en"}],
                    [{"text": "العربية", "callback_data": "set_lang_ar"}, {"text": "Türkçe", "callback_data": "set_lang_tr"}]
                ]}
                send_telegram_message(chat_id, MESSAGES[lang]["language_prompt"], reply_markup=keyboard)
            
            elif command == '/surah':
                handle_surah(chat_id, args, lang)
            
            # Handle reciter commands
            else:
                reciter_command = command.replace('/', '')
                if reciter_command in RECITERS:
                    handle_recitation(chat_id, args, lang, reciter_command)

    except Exception as e:
        # This is a critical catch-all. It logs the error for debugging.
        logging.error(f"!!! CRITICAL ERROR IN WEBHOOK: {e}", exc_info=True)
        # Optionally, notify the admin about the critical failure
        if ADMIN_ID:
            try:
                send_telegram_message(ADMIN_ID, f"🚨 Critical Bot Error 🚨\n\n{e}")
            except:
                pass # Avoid recursive failures

    return 'ok', 200

# A simple health check endpoint for the root URL
@app.route('/', methods=['GET'])
def index():
    return "Quran Bot is running.", 200

# This part is for local testing and not used by Vercel
if __name__ == "__main__":
    app.run(debug=True)
