import os
import requests
import json
from flask import Flask, request

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# --- Environment Variables ---
# ከ BotFather ያገኘነውን ቶክን እናስቀምጣለን
TOKEN = os.environ.get('TELEGRAM_TOKEN')
# *** አዲስ: የእርስዎን የቴሌግራም User ID እዚህ ያስገቡ (Vercel ላይ) ***
ADMIN_ID = os.environ.get('ADMIN_ID')
# *** አዲስ: ተጠቃሚዎች እንዲቀላቀሉ የሚፈልጉትን ቻናል እዚህ ያስገቡ (Vercel ላይ) ***
CHANNEL_ID = os.environ.get('CHANNEL_ID') # Example: '@MyChannelName'

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
        "welcome": "Assalamu 'alaikum,\n\nወደ ቁርአን ቦት በደህና መጡ!\n\n📖 *ለጽሁፍ:*\n`/surah <ቁጥር>`\n`/juz <ቁጥር>`\n\n🔊 *ለድምጽ (ሙሉ ሱራ ሊንክ):*\n`/abdulbasit <ቁጥር>`\n`/yasser <ቁጥር>`\n\n⚙️ *ሌሎች ትዕዛዞች:*\n`/language` - ቋንቋ ለመቀየር\n`/support` - ለእርዳታ",
        "language_prompt": "እባክዎ ቋንቋ ይምረጡ:",
        "language_selected": "✅ ቋንቋ ወደ አማርኛ ተቀይሯል።",
        "support_message": "ለእርዳታ ወይም አስተያየት፣ እባክዎ ወደ @YourSupportUsername መልዕክት ይላኩ።",
        "force_join": "🙏 ቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
        "surah_prompt": "እባкዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/surah 2`",
        "juz_prompt": "እባкዎ ትክክለኛ የጁዝ ቁጥር ያስገቡ (1-30)።\nአጠቃቀም: `/juz 15`",
        "audio_link_message": "🔗 [Download / Play Audio Here]({audio_url})\n\nከላይ ያለውን ሰማያዊ ሊንክ በመጫን ድምጹን በቀጥታ ማዳመጥ ወይም ማውረድ ይችላሉ።",
        "error_fetching": "ይቅርታ፣ የድምጽ ፋይሉን ሊንክ ማግኘት አልቻልኩም።\n\n**ምክንያት:** የድምጽ ፋይሉ በድረ-ገጹ ላይ አልተገኘም (404 Error)።\n**የተሞከረው ሊንክ:** `{full_audio_url}`"
    },
    'en': {
        "welcome": "Assalamu 'alaikum,\n\nWelcome to the Quran Bot!\n\n📖 *For Text:*\n`/surah <number>`\n`/juz <number>`\n\n🔊 *For Audio (Full Surah Link):*\n`/abdulbasit <number>`\n`/yasser <number>`\n\n⚙️ *Other Commands:*\n`/language` - To change language\n`/support` - For help",
        "language_prompt": "Please select a language:",
        "language_selected": "✅ Language changed to English.",
        "support_message": "For support or feedback, please contact @YourSupportUsername.",
        "force_join": "🙏 To use the bot, please join our channel first.",
        "surah_prompt": "Please provide a valid Surah number (1-114).\nUsage: `/surah 2`",
        "juz_prompt": "Please provide a valid Juz' number (1-30).\nUsage: `/juz 15`",
        "audio_link_message": "🔗 [Download / Play Audio Here]({audio_url})\n\nYou can listen or download the audio by clicking the blue link above.",
        "error_fetching": "Sorry, I could not get the audio link.\n\n**Reason:** The audio file was not found on the server (404 Error).\n**Attempted Link:** `{full_audio_url}`"
    },
    'ar': {
        "welcome": "السلام عليكم\n\nأهلاً بك في بوت القرآن!\n\n� *للنص:*\n`/surah <رقم>`\n`/juz <رقم>`\n\n🔊 *للصوت (رابط السورة كاملة):*\n`/abdulbasit <رقم>`\n`/yasser <رقم>`\n\n⚙️ *أوامر أخرى:*\n`/language` - لتغيير اللغة\n`/support` - للمساعدة",
        "language_prompt": "الرجاء اختيار اللغة:",
        "language_selected": "✅ تم تغيير اللغة إلى العربية.",
        "support_message": "للمساعدة أو الاقتراحات، يرجى التواصل مع @YourSupportUsername.",
        "force_join": "🙏 لاستخدام البوت، يرجى الانضمام إلى قناتنا أولاً.",
        "surah_prompt": "الرجاء إدخال رقم سورة صحيح (1-114).\nمثال: `/surah 2`",
        "juz_prompt": "الرجاء إدخال رقم جزء صحيح (1-30).\nمثال: `/juz 15`",
        "audio_link_message": "🔗 [تحميل / تشغيل الصوت هنا]({audio_url})\n\nيمكنك الاستماع أو تحميل الصوت بالضغط على الرابط الأزرق أعلاه.",
        "error_fetching": "عذراً، لم أتمكن من جلب رابط الملف الصوتي.\n\n**السبب:** لم يتم العثور على الملف الصوتي على الخادم (خطأ 404).\n**الرابط الذي تمت تجربته:** `{full_audio_url}`"
    },
    'tr': {
        "welcome": "Esselamu aleyküm,\n\nKuran Bot'a hoş geldiniz!\n\n📖 *Metin İçin:*\n`/surah <numara>`\n`/juz <numara>`\n\n🔊 *Ses İçin (Tam Sure Linki):*\n`/abdulbasit <numara>`\n`/yasser <numara>`\n\n⚙️ *Diğer Komutlar:*\n`/language` - Dili değiştirmek için\n`/support` - Yardım için",
        "language_prompt": "Lütfen bir dil seçin:",
        "language_selected": "✅ Dil Türkçe olarak değiştirildi.",
        "support_message": "Destek veya geri bildirim için lütfen @YourSupportUsername ile iletişime geçin.",
        "force_join": "🙏 Botu kullanmak için lütfen önce kanalımıza katılın.",
        "surah_prompt": "Lütfen geçerli bir Sure numarası girin (1-114).\nKullanım: `/surah 2`",
        "juz_prompt": "Lütfen geçerli bir Cüz numarası girin (1-30).\nKullanım: `/juz 15`",
        "audio_link_message": "🔗 [Sesi İndir / Oynat]({audio_url})\n\nYukarıdaki mavi bağlantıya tıklayarak sesi dinleyebilir veya indirebilirsiniz.",
        "error_fetching": "Üzgünüm, ses bağlantısını alamadım.\n\n**Neden:** Ses dosyası sunucuda bulunamadı (404 Hatası).\n**Denenen Bağlantı:** `{full_audio_url}`"
    }
}

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

# *** አዲስ: ተጠቃሚው ቻናሉን መቀላቀሉን የሚያረጋግጥ ተግባር ***
def is_user_member(user_id):
    if not CHANNEL_ID:
        return True  # ቻናል ካልተቀናበረ፣ ሁሉንም ፍቀድ
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
        return False # Fail-safe
    return False

# ሱራ በጽሁፍ ለመላክ የሚረዳ ተግባር
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

# ጁዝ በጽሁፍ ለመላክ የሚረዳ ተግባር
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

# የድምጽ መላኪያ ተግባር
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
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(full_audio_url, headers=headers, stream=True, timeout=15)
        
        if response.status_code != 200:
            raise Exception(f"File not found, status code: {response.status_code}")

        message_text = MESSAGES[lang]["audio_link_message"].format(audio_url=full_audio_url)
        send_telegram_message(chat_id, message_text)

    except (IndexError, ValueError):
        send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
    except Exception as e:
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(full_audio_url=full_audio_url))

# ዋናው መግቢያ (Webhook)
@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()
    
    # Callback Query (ከቋንቋ ምርጫ ቁልፎች)
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

    # Normal Message
    if 'message' in update:
        message = update['message']
        user_id = message['from']['id']
        chat_id = message['chat']['id']
        text = message.get('text', '').lower()
        command_parts = text.split()
        command = command_parts[0]
        args = command_parts[1:]
        lang = get_user_lang(chat_id)

        # *** አዲስ: የአድሚን እና የቻናል አባልነት ማረጋገጫ ***
        is_admin = str(user_id) == ADMIN_ID
        
        if not is_admin and not is_user_member(user_id):
            channel_name = CHANNEL_ID.replace('@', '')
            keyboard = {
                "inline_keyboard": [
                    [{"text": f"✅ {MESSAGES[lang]['welcome'].splitlines()[0]}", "url": f"https://t.me/{channel_name}"}]
                ]
            }
            send_telegram_message(chat_id, MESSAGES[lang]["force_join"], reply_markup=keyboard)
            return 'ok'

        # --- Command Handling ---
        if command == '/start':
            send_telegram_message(chat_id, MESSAGES[lang]["welcome"])

        elif command == '/language':
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "አማርኛ", "callback_data": "set_lang_am"},
                        {"text": "English", "callback_data": "set_lang_en"}
                    ],
                    [
                        {"text": "العربية", "callback_data": "set_lang_ar"},
                        {"text": "Türkçe", "callback_data": "set_lang_tr"}
                    ]
                ]
            }
            send_telegram_message(chat_id, MESSAGES[lang]["language_prompt"], reply_markup=keyboard)
        
        elif command == '/support':
            send_telegram_message(chat_id, MESSAGES[lang]["support_message"])

        elif command == '/surah': handle_surah(chat_id, args, lang)
        elif command == '/juz': handle_juz(chat_id, args, lang)
        
        reciter_command = command.replace('/', '')
        if reciter_command in RECITERS:
            handle_recitation(chat_id, args, lang, reciter_command)

    return 'ok'

@app.route('/')
def index():
    return "Bot is running with user's selected code and new features!"
