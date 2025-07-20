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
    },
    'ar': {
        "welcome": "🕌 السلام عليكم {username}\n\n📖 أهلاً بك في بوت القرآن!\n\n✍️ لآيات القرآن كنص:\n\n/surah <رقم> — أدخل رقم السورة\n/juz <رقم> — أدخل رقم الجزء\n\n🔊 للصوت (تلاوات السور كاملة):\n/abdulbasit <رقم> �️\n/yasser <رقم> 🎧\n\n⚙️ أوامر أخرى:\n🌐 /language — لتغيير اللغة\n🆘 /support <رسالة> — أرسل رسالة إلى المسؤول للمساعدة",
        "language_prompt": "الرجاء اختيار اللغة:",
        "language_selected": "✅ تم تغيير اللغة إلى العربية.",
        "support_prompt": "الرجاء إدخال رسالتك بعد أمر `/support`.\nمثال: `/support مرحباً، أحتاج إلى مساعدة`",
        "support_sent": "✅ تم إرسال رسالتك إلى المسؤول.",
        "force_join": "🙏 لاستخدام البوت، يرجى الانضمام إلى قناتنا أولاً.",
        "join_button_text": "✅ please first join channel",
        "surah_prompt": "الرجاء إدخال رقم سورة صحيح (1-114).\nمثال: `/surah 2`",
        "juz_prompt": "الرجاء إدخال رقم جزء صحيح (1-30).\nمثال: `/juz 15`",
        "audio_link_message": "🔗 [تحميل / تشغيل الصوت هنا]({audio_url})\n\nيمكنك الاستماع أو تحميل الصوت بالضغط على الرابط الأزرق أعلاه.",
        "error_fetching": "عذراً، لم أتمكن من جلب رابط الملف الصوتي.\n\n**السبب:** لم يتم العثور على الملف الصوتي على الخادم (خطأ 404).\n**الرابط الذي تمت تجربته:** `{full_audio_url}`"
    },
    'tr': {
        "welcome": "🕌 Esselamu aleyküm {username}\n\n📖 Kuran Bot'a hoş geldiniz!\n\n✍️ Metin olarak Kur'an ayetleri için:\n\n/surah <numara> — Sure numarasını girin\n/juz <numara> — Cüz numarasını girin\n\n🔊 Ses İçin (Tam Sure Tilavetleri):\n/abdulbasit <numara> 🎙️\n/yasser <numara> 🎧\n\n⚙️ Diğer Komutlar:\n🌐 /language — Dili değiştirmek için\n🆘 /support <mesaj> — Yardım için yöneticiye mesaj gönderin",
        "language_prompt": "Lütfen bir dil seçin:",
        "language_selected": "✅ Dil Türkçe olarak değiştirildi.",
        "support_prompt": "Lütfen mesajınızı `/support` komutundan sonra girin.\nÖrnek: `/support Merhaba, yardıma ihtiyacım var`",
        "support_sent": "✅ Mesajınız yöneticiye gönderildi.",
        "force_join": "🙏 Botu kullanmak için lütfen önce kanalımıza katılın.",
        "join_button_text": "✅ please first join channel",
        "surah_prompt": "Lütfen geçerli bir Sure numarası girin (1-114).\nKullanım: `/surah 2`",
        "juz_prompt": "Lütfen geçerli bir Cüz numarası girin (1-30).\nKullanım: `/juz 15`",
        "audio_link_message": "🔗 [Sesi İndir / Oynat]({audio_url})\n\nYukarıdaki mavi bağlantıya tıklayarak sesi dinleyebilir veya indirebilirsiniz.",
        "error_fetching": "Üzgünüm, ses bağlantısını alamadım.\n\n**Neden:** Ses dosyası sunucuda bulunamadı (404 Hatası).\n**Denenen Bağlantı:** `{full_audio_url}`"
    }
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
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.Timeout:
        pass

def get_user_lang(chat_id):
    return user_languages.get(chat_id, 'am')

def is_user_member(user_id):
    if not CHANNEL_ID: return True
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember"
        payload = {'chat_id': CHANNEL_ID, 'user_id': user_id}
        response = requests.get(url, params=payload)
        status = response.json()['result']['status']
        return status in ['creator', 'administrator', 'member']
    except Exception: return False

# --- Bot Feature Functions ---
def handle_surah(chat_id, args, lang):
    try:
        surah_number = int(args[0])
        response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}")
        data = response.json()['data']
        surah_name = data['englishName']
        ayahs = data['ayahs']
        message = f"🕋 *Surah {surah_number}: {surah_name}*\n\n"
        for ayah in ayahs: message += f"{ayah['numberInSurah']}. {ayah['text']}\n"
        for i in range(0, len(message), 4096): send_telegram_message(chat_id, message[i:i+4096])
    except Exception: send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])

def handle_juz(chat_id, args, lang):
    try:
        juz_number = int(args[0])
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
        for i in range(0, len(message), 4096): send_telegram_message(chat_id, message[i:i+4096])
    except Exception: send_telegram_message(chat_id, MESSAGES[lang]["juz_prompt"])

def handle_recitation(chat_id, args, lang, reciter_key):
    full_audio_url = ""
    try:
        surah_number = int(args[0])
        reciter_info = RECITERS[reciter_key]
        reciter_name = reciter_info['name']
        reciter_identifier = reciter_info['identifier']
        surah_info_response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}")
        surah_name_english = surah_info_response.json()['data']['englishName']
        padded_surah_number = str(surah_number).zfill(3)
        full_audio_url = f"https://download.quranicaudio.com/quran/{reciter_identifier}/{padded_surah_number}.mp3"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(full_audio_url, headers=headers, stream=True, timeout=15)
        if response.status_code != 200: raise Exception("File not found")
        message_text = MESSAGES[lang]["audio_link_message"].format(audio_url=full_audio_url)
        send_telegram_message(chat_id, message_text)
    except Exception:
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(full_audio_url=full_audio_url))

# --- Admin Commands ---
def handle_status(chat_id):
    try:
        user_count = len(get_db().get('users', []))
        send_telegram_message(chat_id, f"📊 *Bot Status*\n\nTotal Users: *{user_count}*")
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Could not get status. DB Error: `{e}`")

def handle_broadcast(admin_id, message_text):
    try:
        users = get_db().get('users', [])
        sent_count = 0
        for user_id in users:
            try:
                send_telegram_message(user_id, message_text)
                sent_count += 1
                time.sleep(0.1)
            except Exception: pass
        send_telegram_message(admin_id, f"✅ Broadcast sent to *{sent_count}* of *{len(users)}* users.")
    except Exception as e:
        send_telegram_message(admin_id, f"❌ Broadcast failed. DB Error: `{e}`")

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
    try:
        update = request.get_json()
        
        if 'callback_query' in update:
            data = update['callback_query']['data']
            chat_id = update['callback_query']['message']['chat']['id']
            if data.startswith('set_lang_'):
                lang_code = data.split('_')[-1]
                user_languages[chat_id] = lang_code
                send_telegram_message(chat_id, MESSAGES[get_user_lang(chat_id)]["language_selected"])
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

            if command == '/start': send_telegram_message(chat_id, MESSAGES[lang]["welcome"].format(username=user_name))
            elif command == '/language':
                keyboard = {"inline_keyboard": [[{"text": "አማርኛ", "callback_data": "set_lang_am"}, {"text": "English", "callback_data": "set_lang_en"}],[{"text": "العربية", "callback_data": "set_lang_ar"}, {"text": "Türkçe", "callback_data": "set_lang_tr"}]]}
                send_telegram_message(chat_id, MESSAGES[lang]["language_prompt"], reply_markup=keyboard)
            elif command == '/support':
                if not args: send_telegram_message(chat_id, MESSAGES[lang]["support_prompt"])
                else:
                    support_message = " ".join(args)
                    forward_message = f"🆘 *New Support Message*\n\n*From:* {user_name} (ID: `{user_id}`)\n\n*Message:* {support_message}"
                    if ADMIN_ID: send_telegram_message(ADMIN_ID, forward_message)
                    send_telegram_message(chat_id, MESSAGES[lang]["support_sent"])
            elif is_admin and command == '/status': handle_status(chat_id)
            elif is_admin and command == '/broadcast':
                if not args: send_telegram_message(chat_id, "Usage: `/broadcast <message>`")
                else: handle_broadcast(chat_id, " ".join(args))
            elif is_admin and command == '/debug': handle_debug(chat_id)
            elif command == '/surah': handle_surah(chat_id, args, lang)
            elif command == '/juz': handle_juz(chat_id, args, lang)
            else:
                reciter_command = command.replace('/', '')
                if reciter_command in RECITERS:
                    handle_recitation(chat_id, args, lang, reciter_command)
    except Exception as e:
        print(f"!!! CRITICAL ERROR IN WEBHOOK: {e}")

    return 'ok'

@app.route('/')
def index():
    return "Final Bot is running with all features and languages fixed!"
