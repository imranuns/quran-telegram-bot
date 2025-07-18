import os
import requests
import json
from flask import Flask, request
import time

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# ከ BotFather ያገኘነውን ቶክን እናስቀምጣለን
TOKEN = os.environ.get('TELEGRAM_TOKEN')
QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'

# *** የተስተካከለው የቃሪዎች ዝርዝር (ማሂር አል-ሙዓይቅሊ ወጥቷል) ***
RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 'ar.abdulbasitmurattal'},
    'yasser': {'name': 'Yasser Al-Dosari', 'identifier': 'ar.yasseraddousari'}
}

# ቴሌግራም ላይ መልዕክት ለመላክ የሚረዳ ተግባር (function)
def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.Timeout:
        pass

# አዲሱ የድምጽ መላኪያ ተግባር (አንድ በአንድ አንቀጽ)
def send_telegram_audio(chat_id, audio_url, title, performer):
    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
    payload = {
        'chat_id': chat_id,
        'audio': audio_url,
        'title': title,
        'performer': performer
    }
    try:
        requests.post(url, json=payload, timeout=10) # We give it more time
    except requests.exceptions.Timeout:
        pass # It will still send

# ሱራ በጽሁፍ ለመላክ የሚረዳ ተግባር
def handle_surah(chat_id, args):
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
        send_telegram_message(chat_id, "እባክዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/surah 2`")
    except Exception:
        send_telegram_message(chat_id, "ይቅርታ፣ ሱራውን ማግኘት አልቻልኩም።")

# ጁዝ በጽሁፍ ለመላክ የሚረዳ ተግባር
def handle_juz(chat_id, args):
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
        send_telegram_message(chat_id, "እባክዎ ትክክለኛ የጁዝ ቁጥር ያስገቡ (1-30)።\nአጠቃቀም: `/juz 15`")
    except Exception:
        send_telegram_message(chat_id, "ይቅርታ፣ ጁዙን ማግኘት አልቻልኩም።")

# ሙሉ በሙሉ የተቀየረው የድምጽ መላኪያ ተግባር
def handle_recitation(chat_id, args, reciter_key):
    try:
        if not args:
            send_telegram_message(chat_id, f"እባክዎ የሱራ ቁጥር ያስገቡ።\nአጠቃቀም: `/{reciter_key} 2`")
            return

        surah_number = int(args[0])
        if not 1 <= surah_number <= 114: raise ValueError
        
        reciter_info = RECITERS[reciter_key]
        reciter_name = reciter_info['name']
        reciter_identifier = reciter_info['identifier']
        
        # የድምጽ ፋይሉን ከ API ላይ እንጠይቃለን
        audio_response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}/{reciter_identifier}")
        audio_data = audio_response.json()

        if audio_data['code'] != 200:
            raise Exception("Could not fetch audio from the API")

        surah_name_english = audio_data['data']['englishName']
        ayahs = audio_data['data']['ayahs']
        
        send_telegram_message(chat_id, f"🔊 የ *{surah_name_english}* ቅጂ በ *{reciter_name}* መላክ ተጀምሯል...")

        # እያንዳንዱን አንቀጽ እንደ ድምጽ ፋይል እንልካለን
        for ayah in ayahs:
            send_telegram_audio(
                chat_id=chat_id,
                audio_url=ayah['audio'],
                title=f"Ayah {ayah['numberInSurah']}",
                performer=reciter_name
            )
            time.sleep(0.5) # ቴሌግራም እንዳይጨናነቅ ትንሽ ፋታ እንሰጠዋለን

    except (IndexError, ValueError):
        send_telegram_message(chat_id, f"እባкዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/{reciter_key} 2`")
    except Exception as e:
        send_telegram_message(chat_id, "ይቅርታ፣ የድምጽ ፋይሉን ማግኘት አልቻልኩም። እባክዎ እንደገና ይሞክሩ።")

# ዋናው መግቢያ (Webhook)
@app.route('/', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = request.get_json()
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').lower()
            command_parts = text.split()
            command = command_parts[0]
            args = command_parts[1:]

            if command == '/start':
                welcome_message = (
                    "Assalamu 'alaikum,\n\n"
                    "ወደ ቁርአን ቦት በደህና መጡ!\n\n"
                    "📖 *ለጽሁፍ:*\n"
                    "`/surah <ቁጥር>`\n"
                    "`/juz <ቁጥር>`\n\n"
                    "🔊 *ለድምጽ (አንድ በአንድ አንቀጽ):*\n"
                    "`/abdulbasit <ቁጥር>`\n"
                    "`/yasser <ቁጥር>`"
                )
                send_telegram_message(chat_id, welcome_message)
            
            elif command == '/surah': handle_surah(chat_id, args)
            elif command == '/juz': handle_juz(chat_id, args)
            
            reciter_command = command.replace('/', '')
            if reciter_command in RECITERS:
                handle_recitation(chat_id, args, reciter_command)

    return 'ok'

@app.route('/')
def index():
    return "Bot is running with 2 reciters!"
