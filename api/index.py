import os
import requests
import json
from flask import Flask, request

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# ከ BotFather ያገኘነውን ቶክን እናስቀምጣለን
TOKEN = os.environ.get('TELEGRAM_TOKEN')
QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'

# የቃሪዎችን ዝርዝር እና የድምጽ ፋይል መገኛቸውን እናስቀምጣለን
RECITERS = {
    'abdulbasit': {'name': 'Abdul Basit Abdus Samad', 'identifier': 'abdul_basit_murattal'},
    'hussary': {'name': 'Mahmoud Khalil Al-Hussary', 'identifier': 'husary'},
    'minshawi': {'name': 'Muhammad Siddiq Al-Minshawi', 'identifier': 'minshawi'},
    'mishary': {'name': 'Mishary Rashid Alafasy', 'identifier': 'mishaari_raashid_al_afasy'},
    'sudais': {'name': 'Abdul Rahman Al-Sudais', 'identifier': 'abdurrahmaan_as-sudais'},
    'maher': {'name': 'Maher Al-Muaiqly', 'identifier': 'maher_muaiqly'},
    'ghamdi': {'name': 'Saad Al-Ghamdi', 'identifier': 'saad_al-ghamdi'},
    'shuraim': {'name': 'Saud Al-Shuraim', 'identifier': 'saood_ash-shuraym'},
    'yasser': {'name': 'Yasser Al-Dosari', 'identifier': 'yasser_ad-dussary'},
    'ajmi': {'name': 'Ahmed Al-Ajmi', 'identifier': 'ahmed_ibn_ali_al_ajamy'}
}

# ቴሌግራም ላይ መልዕክት ለመላክ የሚረዳ ተግባር (function)
def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    try:
        # ጥያቄውን ከላከ በኋላ ለረጅም ጊዜ እንዳይጠብቅ timeout እንጨምራለን
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.Timeout:
        pass # ችግር የለውም፣ መልዕክቱ ይላካል

# ቴሌግራም ላይ የድምጽ ፋይል ለመላክ የሚረዳ ተግባር
def send_telegram_audio(chat_id, audio_url, title, performer):
    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
    payload = {
        'chat_id': chat_id,
        'audio': audio_url,
        'title': title,
        'performer': performer,
        'caption': f"Recitation of {title} by {performer}"
    }
    try:
        # ጥያቄውን ከላከ በኋላ ለረጅም ጊዜ እንዳይጠብቅ timeout እንጨምራለን
        requests.post(url, json=payload, timeout=5)
    except requests.exceptions.Timeout:
        pass # ችግር የለውም፣ የድምጽ ፋይሉ ይላካል

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

# ለሁሉም ቃሪዎች የሚያገለግል አንድ ወጥ ተግባር
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
        
        surah_info_response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}")
        surah_data = surah_info_response.json()['data']
        surah_name_english = surah_data['englishName']
        
        send_telegram_message(chat_id, f"የ *{surah_name_english}* ሙሉ የድምጽ ፋይል በ *{reciter_name}* በማዘጋጀት ላይ ነው... እባክዎ ትንሽ ይጠብቁ።")

        padded_surah_number = str(surah_number).zfill(3)
        full_audio_url = f"https://download.quranicaudio.com/quran/{reciter_identifier}/{padded_surah_number}.mp3"
        
        send_telegram_audio(chat_id=chat_id, audio_url=full_audio_url, title=f"Surah {surah_name_english}", performer=reciter_name)

    except (IndexError, ValueError):
        send_telegram_message(chat_id, f"እባክዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/{reciter_key} 2`")
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
                    "ወደ ቁርአን ቦት በደህና መጡ! (10 ቃሪዎች ተጨምረዋል)\n\n"
                    "📖 *ለጽሁፍ:*\n"
                    "`/surah <ቁጥር>`\n"
                    "`/juz <ቁጥር>`\n\n"
                    "🔊 *ለድምጽ (ሙሉ ሱራ):*\n"
                    "`/abdulbasit <ቁጥር>`\n"
                    "`/hussary <ቁጥር>`\n"
                    "`/minshawi <ቁጥር>`\n"
                    "`/mishary <ቁጥር>`\n"
                    "`/sudais <ቁጥር>`\n"
                    "`/maher <ቁጥር>`\n"
                    "`/ghamdi <ቁጥር>`\n"
                    "`/shuraim <ቁጥር>`\n"
                    "`/yasser <ቁጥር>`\n"
                    "`/ajmi <ቁጥር>`"
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
    return "Bot is running with timeout fix!"
