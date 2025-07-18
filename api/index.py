import os
import requests
import json
from flask import Flask, request

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# ከ BotFather ያገኘነውን ቶክን እናስቀምጣለን
TOKEN = os.environ.get('TELEGRAM_TOKEN')
QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'

# *** የተስተካከለው የቃሪዎች ዝርዝር ***
RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 'abdul_basit_murattal'},
    'minshawi': {'name': 'Muhammad Siddiq Al-Minshawi', 'identifier': 'minshawi_murattal'}, # FIXED
    'mishary': {'name': 'Mishary Rashid Alafasy', 'identifier': 'alafasy'} # Correct identifier
}

# ቴሌግራም ላይ መልዕክት ለመላክ የሚረዳ ተግባር (function)
def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    try:
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.Timeout:
        pass

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

# የተሻሻለው የድምጽ መላኪያ ተግባር (ሊንኩን ከመላኩ በፊት ያረጋግጣል)
def handle_recitation(chat_id, args, reciter_key):
    full_audio_url = "" # Define url variable to be accessible in except block
    try:
        if not args:
            send_telegram_message(chat_id, f"እባክዎ የሱራ ቁጥር ያስገቡ።\nአጠቃቀም: `/{reciter_key} 2`")
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
        
        # ሊንኩን ከመላካችን በፊት መስራቱን እናረጋግጣለን
        response = requests.head(full_audio_url, timeout=10)
        if response.status_code != 200:
            # ሊንኩ የማይሰራ ከሆነ ስህተት እንፈጥራለን
            raise Exception(f"File not found, status code: {response.status_code}")

        # ሊንኩ የሚሰራ ከሆነ እንልካለን
        message_text = (
            f"🔊 *Surah {surah_name_english}* by *{reciter_name}*\n\n"
            f"🔗 [Download / Play Audio Here]({full_audio_url})\n\n"
            f"ከላይ ያለውን ሰማያዊ ሊንክ በመጫን ድምጹን በቀጥታ ማዳመጥ ወይም ማውረድ ይችላሉ።"
        )
        send_telegram_message(chat_id, message_text)

    except (IndexError, ValueError):
        send_telegram_message(chat_id, f"እባкዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/{reciter_key} 2`")
    except Exception as e:
        # ዝርዝር የስህተት መልዕክት እንልካለን
        error_message = (
            "ይቅርታ፣ የድምጽ ፋይሉን ሊንክ ማግኘት አልቻልኩም።\n\n"
            f"**ምክንያት:** የድምጽ ፋይሉ በድረ-ገጹ ላይ አልተገኘም (404 Error)።\n"
            f"**የተሞከረው ሊንክ:** `{full_audio_url}`"
        )
        send_telegram_message(chat_id, error_message)

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
                    "ወደ ቁርአን ቦት በደህና መጡ! (3 ቃሪዎች)\n\n"
                    "📖 *ለጽሁፍ:*\n"
                    "`/surah <ቁጥር>`\n"
                    "`/juz <ቁጥር>`\n\n"
                    "🔊 *ለድምጽ (ሙሉ ሱራ ሊንክ):*\n"
                    "`/abdulbasit <ቁጥር>`\n"
                    "`/minshawi <ቁጥር>`\n"
                    "`/mishary <ቁጥር>`"
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
    return "Bot is running with FINAL reciter fix!"
