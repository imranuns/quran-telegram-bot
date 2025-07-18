import os
import requests
import json
from flask import Flask, request

# Flask መተግበሪያ መፍጠር
app = Flask(__name__)

# ከ BotFather ያገኘነውን ቶክን እናስቀምጣለን (ይህንን በኋላ Vercel ላይ እናስተካክለዋለን)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
QURAN_API_BASE_URL = 'http://api.alquran.cloud/v1'

# ቴሌግራም ላይ መልዕክት ለመላክ የሚረዳ ተግባር (function)
def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    requests.post(url, json=payload)

# ቴሌግራም ላይ የድምጽ ፋይል ለመላክ የሚረዳ ተግባር
def send_telegram_audio(chat_id, audio_url, title, performer):
    url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
    payload = {
        'chat_id': chat_id,
        'audio': audio_url,
        'title': title,
        'performer': performer
    }
    requests.post(url, json=payload)

# ሱራ ለመላክ የሚረዳ ተግባር
def handle_surah(chat_id, args):
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114:
            raise ValueError
        
        response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}")
        data = response.json()['data']
        surah_name = data['englishName']
        ayahs = data['ayahs']

        message = f"🕋 *Surah {surah_number}: {surah_name}*\n\n"
        for ayah in ayahs:
            message += f"{ayah['numberInSurah']}. {ayah['text']}\n"
        
        # የቴሌግራም መልዕክት መጠን ገደብ ስላለው፣ ረጅም ሱራዎችን ከፋፍለን እንልካለን
        for i in range(0, len(message), 4096):
            send_telegram_message(chat_id, message[i:i+4096])

    except (IndexError, ValueError):
        send_telegram_message(chat_id, "እባክዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/surah 2`")
    except Exception:
        send_telegram_message(chat_id, "ይቅርታ፣ ሱራውን ማግኘት አልቻልኩም። እባክዎ እንደገና ይሞክሩ።")

# ጁዝ ለመላክ የሚረዳ ተግባር
def handle_juz(chat_id, args):
    try:
        juz_number = int(args[0])
        if not 1 <= juz_number <= 30:
            raise ValueError

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

# የድምጽ ፋይል (recitation) ለመላክ የሚረዳ ተግባር
def handle_mahir(chat_id, args):
    try:
        surah_number = int(args[0])
        if not 1 <= surah_number <= 114:
            raise ValueError
        
        reciter_id = 'ar.mahermuaiqly'
        reciter_name = 'Maher Al Muaiqly'
        
        send_telegram_message(chat_id, f"የሱራ {surah_number} የድምጽ ፋይል በማዘጋጀት ላይ ነው... እባክዎ ትንሽ ይጠብቁ።")

        response = requests.get(f"{QURAN_API_BASE_URL}/surah/{surah_number}/{reciter_id}")
        data = response.json()['data']
        surah_name = data['englishName']
        ayahs = data['ayahs']
        
        send_telegram_message(chat_id, f"🔊 *ሱራ {surah_number}: {surah_name}* በቃሪዕ *{reciter_name}*")
        for ayah in ayahs:
            send_telegram_audio(
                chat_id=chat_id,
                audio_url=ayah['audio'],
                title=f"አያህ {ayah['numberInSurah']}",
                performer=reciter_name
            )
    except (IndexError, ValueError):
        send_telegram_message(chat_id, "እባክዎ ትክክለኛ የሱራ ቁጥር ያስገቡ (1-114)።\nአጠቃቀም: `/mahir_al_muaqily 2`")
    except Exception:
        send_telegram_message(chat_id, "ይቅርታ፣ የድምጽ ፋይሉን ማግኘት አልቻልኩም።")

# Vercel ላይ ዲፕሎይ ስናደርግ ዋናው መግቢያ ይሄ ነው
@app.route('/', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = request.get_json()
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')

            if text.startswith('/start'):
                welcome_message = (
                    f"Assalamu 'alaikum,\n\n"
                    "ወደ ቁርአን ቦት በደህና መጡ!\n\n"
                    "የሚከተሉትን ኮማንዶች መጠቀም ይችላሉ:\n"
                    "📖 `/surah <ቁጥር>` - ሱራ ለማግኘት\n"
                    "📗 `/juz <ቁጥር>` - ጁዝ ለማግኘት\n"
                    "🔊 `/mahir_al_muaqily <የሱራ ቁጥር>` - በማሂር አል-ሙዓይቅሊ ድምጽ ሱራ ለማግኘት"
                )
                send_telegram_message(chat_id, welcome_message)

            elif text.startswith('/surah'):
                args = text.split()[1:]
                handle_surah(chat_id, args)
            
            elif text.startswith('/juz'):
                args = text.split()[1:]
                handle_juz(chat_id, args)

            elif text.startswith('/mahir_al_muaqily'):
                args = text.split()[1:]
                handle_mahir(chat_id, args)

    return 'ok'

# ይህ ክፍል Vercel ዌብሁኩን እንዲያገኝ ይረዳል
@app.route('/')
def index():
    return "Bot is running!"
