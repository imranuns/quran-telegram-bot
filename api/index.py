import os
import requests
import json
import logging
import time
from flask import Flask, request
from pathlib import Path

# --- Basic Configuration ---
# Set up logging to see detailed output in your Vercel logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Load Environment Variables from .env file if it exists ---
def load_env_file():
    """Load environment variables from .env file for local development"""
    env_file = Path('.env')
    if env_file.exists():
        logging.info("Loading environment variables from .env file")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env file if running locally
load_env_file()

# --- Environment Variables ---
# It's crucial that these are all set correctly in your Vercel project settings or .env file.
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY')
JSONBIN_BIN_ID = os.environ.get('JSONBIN_BIN_ID')

# --- Environment Validation ---
def validate_environment():
    """Check if all required environment variables are set"""
    required_vars = {
        'TELEGRAM_TOKEN': TOKEN,
        'ADMIN_ID': ADMIN_ID,
        'JSONBIN_API_KEY': JSONBIN_API_KEY,
        'JSONBIN_BIN_ID': JSONBIN_BIN_ID
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value or var_value.startswith('your_'):
            missing_vars.append(var_name)
    
    if missing_vars:
        error_msg = f"❌ CRITICAL ERROR: Missing environment variables: {', '.join(missing_vars)}"
        logging.error(error_msg)
        logging.error("📋 Please set these variables in your environment or .env file:")
        for var in missing_vars:
            logging.error(f"   - {var}")
        logging.error("📖 See README.md for setup instructions")
        return False
    
    logging.info("✅ All required environment variables are configured")
    return True

# Validate environment on startup
ENV_VALID = validate_environment()

# --- Constants ---
QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'
RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 'abdul_basit_murattal'},
    'yasser': {'name': 'Yasser Al-Dosari', 'identifier': 'yasser_ad-dussary'},
}

# --- All Bot Text in One Place ---
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
        "welcome": "🕌 Assalamu Alaikum {username}\n\n📖 Welcome to the Quran Bot!\n\n✍️ For Quran verses in text:\n\n/surah <number> — Enter Surah number\n/juz <number> — Enter Juz' number\n\n🔊 For Audio (Full Surah Recitations):\n/abdulbasit <number> �️\n/yasser <number> 🎧\n\n⚙️ Other Commands:\n🌐 /language — To change language\n🆘 /support <message> — Send a message to the admin for help",
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
    'ar': {
        "welcome": "🕌 السلام عليكم {username}\n\n📖 أهلاً بك في بوت القرآن!\n\n✍️ لآيات القرآن كنص:\n\n/surah <رقم> — أدخل رقم السورة\n/juz <رقم> — أدخل رقم الجزء\n\n🔊 للصوت (تلاوات السور كاملة):\n/abdulbasit <رقم> 🎙️\n/yasser <رقم> 🎧\n\n⚙️ أوامر أخرى:\n🌐 /language — لتغيير اللغة\n🆘 /support <رسالة> — أرسل رسالة إلى المسؤول للمساعدة",
        "language_prompt": "الرجاء اختيار اللغة:",
        "language_selected": "✅ تم تغيير اللغة إلى العربية.",
        "support_prompt": "الرجاء إدخال رسالتك بعد أمر `/support`.\nمثال: `/support مرحباً، أحتاج إلى مساعدة`",
        "support_sent": "✅ تم إرسال رسالتك إلى المسؤول.",
        "force_join": "🙏 لاستخدام البوت، يرجى الانضمام إلى قناتنا أولاً.",
        "join_button_text": "✅ انضم إلى القناة",
        "surah_prompt": "الرجاء إدخال رقم سورة صحيح (1-114).\nمثال: `/surah 2`",
        "juz_prompt": "الرجاء إدخال رقم جزء صحيح (1-30).\nمثال: `/juz 15`",
        "reciter_prompt": "الرجاء إدخال رقم السورة بعد اسم القارئ (1-114).\nمثال: `/{reciter_key} 2`",
        "audio_link_message": "🎧 *{reciter_name}*\n📖 *سورة {surah_name}*\n\n🔗 [تحميل / تشغيل الصوت هنا]({audio_url})\n\nيمكنك الاستماع أو تحميل الصوت بالضغط على الرابط الأزرق أعلاه.",
        "error_fetching_audio": "عذراً، لم أتمكن من جلب رابط الملف الصوتي.\n\n**السبب:** لم يتم العثور على الملف الصوتي على الخادم (خطأ 404).\n**الرابط الذي تمت تجربته:** `{full_audio_url}`",
        "generic_error": "❌ حدث خطأ. يرجى المحاولة مرة أخرى في وقت لاحق. إذا استمرت المشكلة، اتصل بالمسؤول."
    },
    'tr': {
        "welcome": "🕌 Esselamu aleyküm {username}\n\n📖 Kuran Bot'a hoş geldiniz!\n\n✍️ Metin olarak Kur'an ayetleri için:\n\n/surah <numara> — Sure numarasını girin\n/juz <numara> — Cüz numarasını girin\n\n🔊 Ses İçin (Tam Sure Tilavetleri):\n/abdulbasit <numara> 🎙️\n/yasser <numara> 🎧\n\n⚙️ Diğer Komutlar:\n🌐 /language — Dili değiştirmek için\n🆘 /support <mesaj> — Yardım için yöneticiye mesaj gönderin",
        "language_prompt": "Lütfen bir dil seçin:",
        "language_selected": "✅ Dil Türkçe olarak değiştirildi.",
        "support_prompt": "Lütfen mesajınızı `/support` komutundan sonra girin.\nÖrnek: `/support Merhaba, yardıma ihtiyacım var`",
        "support_sent": "✅ Mesajınız yöneticiye gönderildi.",
        "force_join": "🙏 Botu kullanmak için lütfen önce kanalımıza katılın.",
        "join_button_text": "✅ Kanala Katıl",
        "surah_prompt": "Lütfen geçerli bir Sure numarası girin (1-114).\nKullanım: `/surah 2`",
        "juz_prompt": "Lütfen geçerli bir Cüz numarası girin (1-30).\nKullanım: `/juz 15`",
        "reciter_prompt": "Lütfen okuyucunun adından sonra Sure numarasını girin (1-114).\nKullanım: `/{reciter_key} 2`",
        "audio_link_message": "🎧 *{reciter_name}*\n📖 *Sure {surah_name}*\n\n🔗 [Sesi İndir / Oynat]({audio_url})\n\nYukarıdaki mavi bağlantıya tıklayarak sesi dinleyebilir veya indirebilirsiniz.",
        "error_fetching_audio": "Üzgünüm, ses bağlantısını alamadım.\n\n**Neden:** Ses dosyası sunucuda bulunamadı (404 Hatası).\n**Denenen Bağlantı:** `{full_audio_url}`",
        "generic_error": "❌ Bir hata oluştu. Lütfen daha sonra tekrar deneyin. Sorun devam ederse, yöneticiyle iletişime geçin."
    }
}


# --- Database Functions (JSONBin.io) ---
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
        return {'lang': 'am'}

def set_user_lang(user_id, lang_code):
    """Adds a user or updates their language in the database."""
    try:
        db_data = get_db()
        if 'users' not in db_data:
            db_data['users'] = {}
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
    """Checks if a user is a member of the specified channel."""
    if not CHANNEL_ID:
        return True
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
        payload = {'chat_id': CHANNEL_ID, 'user_id': user_id}
        response = requests.get(url, params=payload, timeout=5)
        response.raise_for_status()
        status = response.json().get('result', {}).get('status')
        return status in ['creator', 'administrator', 'member']
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not check membership for user {user_id}: {e}")
        return False


# --- Bot Feature Functions ---
def handle_surah(chat_id, args, lang):
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114: raise ValueError("Invalid Surah number")
        response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}", timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        surah_name = data['englishName']
        ayahs = data['ayahs']
        message = f"🕋 *Surah {surah_number}: {surah_name}*\n\n"
        for ayah in ayahs: message += f"{ayah['numberInSurah']}. {ayah['text']}\n"
        for i in range(0, len(message), 4096): send_telegram_message(chat_id, message[i:i+4096])
    except (ValueError, IndexError):
        send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
    except (requests.exceptions.RequestException, KeyError) as e:
        logging.error(f"API error fetching surah {args[0] if args else 'N/A'}: {e}")
        send_telegram_message(chat_id, MESSAGES[lang]["generic_error"])

def handle_juz(chat_id, args, lang):
    try:
        juz_number = int(args[0])
        if not 1 <= juz_number <= 30: raise ValueError("Invalid Juz number")
        response = requests.get(f"{QURAN_API_BASE_URL}/juz/{juz_number}", timeout=10)
        response.raise_for_status()
        data = response.json()['data']
        ayahs = data['ayahs']
        message = f"📗 *Juz' {juz_number}*\n\n"
        current_surah_name = ""
        for ayah in ayahs:
            if ayah['surah']['name'] != current_surah_name:
                current_surah_name = ayah['surah']['name']
                message += f"\n--- {current_surah_name} ---\n"
            message += f"{ayah['numberInSurah']}. {ayah['text']}\n"
        for i in range(0, len(message), 4096): send_telegram_message(chat_id, message[i:i+4096])
    except (ValueError, IndexError):
        send_telegram_message(chat_id, MESSAGES[lang]["juz_prompt"])
    except (requests.exceptions.RequestException, KeyError) as e:
        logging.error(f"API error fetching juz {args[0] if args else 'N/A'}: {e}")
        send_telegram_message(chat_id, MESSAGES[lang]["generic_error"])

def handle_recitation(chat_id, args, lang, reciter_key):
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114: raise ValueError("Invalid Surah number")
        reciter_info = RECITERS[reciter_key]
        padded_surah_number = str(surah_number).zfill(3)
        full_audio_url = f"https://download.quranicaudio.com/quran/{reciter_info['identifier']}/{padded_surah_number}.mp3"
        surah_info_response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}", timeout=10)
        surah_info_response.raise_for_status()
        surah_name_english = surah_info_response.json()['data']['englishName']
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(full_audio_url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            logging.warning(f"Audio file not found (HTTP {response.status_code}) at {full_audio_url}")
            send_telegram_message(chat_id, MESSAGES[lang]["error_fetching_audio"].format(full_audio_url=full_audio_url))
            return
        message_text = MESSAGES[lang]["audio_link_message"].format(reciter_name=reciter_info['name'], surah_name=surah_name_english, audio_url=full_audio_url)
        send_telegram_message(chat_id, message_text)
    except (ValueError, IndexError):
        send_telegram_message(chat_id, MESSAGES[lang]["reciter_prompt"].format(reciter_key=reciter_key))
    except (requests.exceptions.RequestException, KeyError) as e:
        logging.error(f"Error fetching recitation for surah {args[0] if args else 'N/A'}: {e}")
        send_telegram_message(chat_id, MESSAGES[lang]["generic_error"])


# --- Admin Commands ---
def handle_status(chat_id):
    try:
        db_data = get_db()
        user_count = len(db_data.get('users', {}))
        send_telegram_message(chat_id, f"📊 *Bot Status*\n\nTotal Users: *{user_count}*")
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        send_telegram_message(chat_id, f"❌ Could not get status. DB Error: `{e}`")

def handle_broadcast(admin_id, message_text):
    try:
        db_data = get_db()
        users = db_data.get('users', {}).keys()
        if not users:
            send_telegram_message(admin_id, "No users in the database to broadcast to.")
            return
        sent_count = 0
        total_users = len(users)
        send_telegram_message(admin_id, f"📣 Starting broadcast to {total_users} users...")
        for user_id in users:
            try:
                send_telegram_message(user_id, message_text)
                sent_count += 1
                time.sleep(0.1) # Avoid hitting rate limits
            except Exception as e:
                logging.error(f"Failed to send broadcast to user {user_id}: {e}")
        send_telegram_message(admin_id, f"✅ Broadcast finished. Sent to *{sent_count}* of *{total_users}* users.")
    except Exception as e:
        logging.error(f"Broadcast failed: {e}")
        send_telegram_message(admin_id, f"❌ Broadcast failed. DB Error: `{e}`")


# --- Webhook Handler ---
@app.route('/', methods=['POST'])
def webhook():
    # Check if environment is properly configured
    if not ENV_VALID:
        logging.error("❌ Webhook called but environment variables are missing!")
        return 'Configuration Error: Missing environment variables', 500
    
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

            if not text.startswith('/'): return 'ok', 200

            user_data = get_user_data(user_id)
            lang = user_data.get('lang', 'am')
            is_admin = str(user_id) == ADMIN_ID

            if not is_admin and not is_user_member(user_id):
                channel_name = CHANNEL_ID.replace('@', '') if CHANNEL_ID else ''
                if channel_name:
                    keyboard = {"inline_keyboard": [[{"text": MESSAGES[lang]["join_button_text"], "url": f"https://t.me/{channel_name}"}]]}
                    send_telegram_message(chat_id, MESSAGES[lang]["force_join"], reply_markup=keyboard)
                else:
                    send_telegram_message(chat_id, MESSAGES[lang]["force_join"])
                return 'ok', 200

            command_parts = text.split()
            command = command_parts[0].lower()
            args = command_parts[1:]

            if command == '/start':
                set_user_lang(user_id, lang)
                send_telegram_message(chat_id, MESSAGES[lang]["welcome"].format(username=user_name))
            elif command == '/language':
                keyboard = {"inline_keyboard": [[{"text": "አማርኛ", "callback_data": "set_lang_am"}, {"text": "English", "callback_data": "set_lang_en"}], [{"text": "العربية", "callback_data": "set_lang_ar"}, {"text": "Türkçe", "callback_data": "set_lang_tr"}]]}
                send_telegram_message(chat_id, MESSAGES[lang]["language_prompt"], reply_markup=keyboard)
            elif command == '/surah':
                handle_surah(chat_id, args, lang)
            elif command == '/juz':
                handle_juz(chat_id, args, lang)
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
                    send_telegram_message(chat_id, "Usage: `/broadcast <message>`")
                else:
                    handle_broadcast(chat_id, " ".join(args))
            else:
                reciter_command = command.replace('/', '')
                if reciter_command in RECITERS:
                    handle_recitation(chat_id, args, lang, reciter_command)

    except Exception as e:
        logging.error(f"!!! CRITICAL ERROR IN WEBHOOK: {e}", exc_info=True)
        if ADMIN_ID:
            try:
                send_telegram_message(ADMIN_ID, f"🚨 Critical Bot Error 🚨\n\nAn error occurred: {e}")
            except:
                pass
    return 'ok', 200

@app.route('/', methods=['GET'])
def index():
    if not ENV_VALID:
        return """
        <h1>🕌 Quran Bot - Configuration Error</h1>
        <p><strong>❌ Bot is not running due to missing environment variables.</strong></p>
        <h2>Required Environment Variables:</h2>
        <ul>
            <li>TELEGRAM_TOKEN - Get from @BotFather on Telegram</li>
            <li>ADMIN_ID - Your Telegram user ID (numeric)</li>
            <li>JSONBIN_API_KEY - Get from JSONBin.io</li>
            <li>JSONBIN_BIN_ID - Your JSONBin.io bin ID</li>
            <li>CHANNEL_ID - Optional: Channel users must join</li>
        </ul>
        <h2>Setup Instructions:</h2>
        <ol>
            <li>Set the environment variables in your hosting platform</li>
            <li>Or create a .env file for local development</li>
            <li>See README.md for detailed instructions</li>
        </ol>
        """, 500
    else:
        return """
        <h1>🕌 Quran Bot</h1>
        <p><strong>✅ Bot is running and properly configured!</strong></p>
        <p>Your Telegram bot is ready to receive messages.</p>
        """, 200

if __name__ == "__main__":
    app.run(debug=True)
