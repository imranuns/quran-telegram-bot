import os
import requests
import json
from flask import Flask, request

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# ከ BotFather ያገኘነውን ቶክን እናስቀምጣለን
TOKEN = os.environ.get('TELEGRAM_TOKEN')
QURAN_TEXT_API_URL = 'http://api.alquran.cloud/v1'
QURAN_AUDIO_API_URL = 'https://api.quran.com/api/v4'

# የቃሪዎች ዝርዝር (ከአዲሱ API)
RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 7},
    'yasser': {'name': 'Yasser Al-Dosari', 'identifier': 11}
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
        "surah_prompt": "እባክዎ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/surah 2`",
        "juz_prompt": "እባкዎ ትክክለኛ የጁዝ ቁጥር ያስገቡ (1-30)።\nአጠቃቀም: `/juz 15`",
        "fetching_audio": "🔊 የ *{surah_name}* ቅጂ በ *{reciter_name}* በማዘጋጀት ላይ ነው...",
        "audio_link_message": "🔗 [Download / Play Audio Here]({audio_url})\n\nከላይ ያለውን ሰማያዊ ሊንክ በመጫን ድምጹን በቀጥታ ማዳመጥ ወይም ማውረድ ይችላሉ።",
        "error_fetching": "ይቅርታ፣ የድምጽ ፋይሉን ማግኘት አልቻልኩም። እባክዎ እንደገና ይሞክሩ።\n\nስህተት: {e}"
    },
    'en': {
        "welcome": "Assalamu 'alaikum,\n\nWelcome to the Quran Bot!\n\n📖 *For Text:*\n`/surah <number>`\n`/juz <number>`\n\n🔊 *For Audio (Full Surah Link):*\n`/abdulbasit <number>`\n`/yasser <number>`\n\n⚙️ *Other Commands:*\n`/language` - To change language\n`/support` - For help",
        "language_prompt": "Please select a language:",
        "language_selected": "✅ Language changed to English.",
        "support_message": "For support or feedback, please contact @YourSupportUsername.",
        "surah_prompt": "Please provide a valid Surah number (1-114).\nUsage: `/surah 2`",
        "juz_prompt": "Please provide a valid Juz' number (1-30).\nUsage: `/juz 15`",
        "fetching_audio": "🔊 Fetching audio of *{surah_name}* by *{reciter_name}*...",
        "audio_link_message": "🔗 [Download / Play Audio Here]({audio_url})\n\nYou can listen or download the audio by clicking the blue link above.",
        "error_fetching": "Sorry, I could not fetch the audio. Please try again.\n\nError: {e}"
    },
    'ar': {
        "welcome": "السلام عليكم\n\nأهلاً بك في بوت القرآن!\n\n📖 *للنص:*\n`/surah <رقم>`\n`/juz <رقم>`\n\n🔊 *للصوت (رابط السورة كاملة):*\n`/abdulbasit <رقم>`\n`/yasser <رقم>`\n\n⚙️ *أوامر أخرى:*\n`/language` - لتغيير اللغة\n`/support` - للمساعدة",
        "language_prompt": "الرجاء اختيار اللغة:",
        "language_selected": "✅ تم تغيير اللغة إلى العربية.",
        "support_message": "للمساعدة أو الاقتراحات، يرجى التواصل مع @YourSupportUsername.",
        "surah_prompt": "الرجاء إدخال رقم سورة صحيح (1-114).\nمثال: `/surah 2`",
        "juz_prompt": "الرجاء إدخال رقم جزء صحيح (1-30).\nمثال: `/juz 15`",
        "fetching_audio": "🔊 جاري تحضير صوت *{surah_name}* بصوت *{reciter_name}*...",
        "audio_link_message": "🔗 [تحميل / تشغيل الصوت هنا]({audio_url})\n\nيمكنك الاستماع أو تحميل الصوت بالضغط على الرابط الأزرق أعلاه.",
        "error_fetching": "عذراً، لم أتمكن من جلب الملف الصوتي. يرجى المحاولة مرة أخرى.\n\nخطأ: {e}"
    },
    'tr': {
        "welcome": "Esselamu aleyküm,\n\nKuran Bot'a hoş geldiniz!\n\n📖 *Metin İçin:*\n`/surah <numara>`\n`/juz <numara>`\n\n🔊 *Ses İçin (Tam Sure Linki):*\n`/abdulbasit <numara>`\n`/yasser <numara>`\n\n⚙️ *Diğer Komutlar:*\n`/language` - Dili değiştirmek için\n`/support` - Yardım için",
        "language_prompt": "Lütfen bir dil seçin:",
        "language_selected": "✅ Dil Türkçe olarak değiştirildi.",
        "support_message": "Destek veya geri bildirim için lütfen @YourSupportUsername ile iletişime geçin.",
        "surah_prompt": "Lütfen geçerli bir Sure numarası girin (1-114).\nKullanım: `/surah 2`",
        "juz_prompt": "Lütfen geçerli bir Cüz numarası girin (1-30).\nKullanım: `/juz 15`",
        "fetching_audio": "🔊 *{reciter_name}* tarafından okunan *{surah_name}* suresinin sesi hazırlanıyor...",
        "audio_link_message": "🔗 [Sesi İndir / Oynat]({audio_url})\n\nYukarıdaki mavi bağlantıya tıklayarak sesi dinleyebilir veya indirebilirsiniz.",
        "error_fetching": "Üzgünüm, ses dosyasını getiremedim. Lütfen tekrar deneyin.\n\nHata: {e}"
    }
}


# ቴሌግራም ላይ መልዕክት ለመላክ የሚረዳ ተግባር
def send_telegram_message(chat_id, text, parse_mode="Markdown", reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.Timeout:
        pass

def get_user_lang(chat_id):
    return user_languages.get(chat_id, 'am') # Default to Amharic

# ሱራ በጽሁፍ ለመላክ የሚረዳ ተግባር
def handle_surah(chat_id, args, lang):
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114: raise ValueError
        response = requests.get(f"{QURAN_TEXT_API_URL}/surah/{surah_number}")
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
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(e=""))

# ጁዝ በጽሁፍ ለመላክ የሚረዳ ተግባር
def handle_juz(chat_id, args, lang):
    try:
        juz_number = int(args[0])
        if not 1 <= juz_number <= 30: raise ValueError
        response = requests.get(f"{QURAN_TEXT_API_URL}/juz/{juz_number}")
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
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(e=""))

# የድምጽ መላኪያ ተግባር
def handle_recitation(chat_id, args, lang, reciter_key):
    try:
        if not args:
            send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
            return

        surah_number = int(args[0])
        if not 1 <= surah_number <= 114: raise ValueError
        
        reciter_info = RECITERS[reciter_key]
        reciter_name = reciter_info['name']
        reciter_id = reciter_info['identifier']
        
        surah_info_response = requests.get(f"{QURAN_TEXT_API_URL}/surah/{surah_number}")
        surah_name_english = surah_info_response.json()['data']['englishName']
        
        send_telegram_message(chat_id, MESSAGES[lang]["fetching_audio"].format(surah_name=surah_name_english, reciter_name=reciter_name))

        audio_api_url = f"{QURAN_AUDIO_API_URL}/recitations/{reciter_id}/by_surah/{surah_number}"
        audio_response = requests.get(audio_api_url)
        audio_response.raise_for_status()

        audio_files = audio_response.json().get('audio_files')
        if not audio_files:
            raise Exception("Audio URL not found in API response.")

        audio_url = audio_files[0]['url']
        
        message_text = MESSAGES[lang]["audio_link_message"].format(audio_url=audio_url)
        send_telegram_message(chat_id, message_text)

    except (IndexError, ValueError):
        send_telegram_message(chat_id, MESSAGES[lang]["surah_prompt"])
    except Exception as e:
        send_telegram_message(chat_id, MESSAGES[lang]["error_fetching"].format(e=e))

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
        chat_id = message['chat']['id']
        text = message.get('text', '').lower()
        command_parts = text.split()
        command = command_parts[0]
        args = command_parts[1:]
        lang = get_user_lang(chat_id)

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
    return "Bot is running with new API and multi-language support!"
