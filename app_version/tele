import logging
import httpx
import os
import threading
import json
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 1. إعداد السيرفر الوهمي لـ Render
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Serviceable!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. قائمة المفاتيح (Key Rotation)
API_KEYS = [
    "AIzaSyDR189t8qPWoycqsgsv_4O1rPa-5y9z2mg",
    "AIzaSyDsG5lrf7LXZIojTV0A2Q_jAV41D9hecAE",
    "AIzaSyAC2SPvOZH3IYySBmuJKZ_T3UvD8HL--H4",
    "AIzaSyDAuBdAUQVeF-GXVglKWruLiuGwt3zyWzY",
    "AIzaSyDRwTEOtxPP-gXNCHAPyuKbTOHHCV0-KUU"
]

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8766269475:AAGF6XecWHqHWHPXW8LWYWOXHwG8tYwRTmg")

# 3. دالة جلب البيانات من مجلد data
def load_data():
    data_path = "data/"
    content = ""
    # ملفات النص
    for file_name in ['faq.md', 'policies.md', 'prompt.txt']:
        try:
            with open(os.path.join(data_path, file_name), 'r', encoding='utf-8') as f:
                content += f"\n--- {file_name.upper()} ---\n{f.read()}\n"
        except: pass
    # ملفات JSON
    for file_name in ['company.json', 'products.json', 'services.json']:
        try:
            with open(os.path.join(data_path, file_name), 'r', encoding='utf-8') as f:
                data_json = json.load(f)
                content += f"\n--- {file_name.upper()} ---\n{json.dumps(data_json, ensure_ascii=False, indent=2)}\n"
        except: pass
    return content

BASE_KNOWLEDGE = load_data()

async def get_gemini_response(payload):
    """دالة تحاول استخدام المفاتيح بالترتيب في حال فشل أحدها"""
    for index, key in enumerate(API_KEYS):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=60.0)
                result = response.json()
                
                if response.status_code == 200 and "candidates" in result:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    logging.warning(f"Key {index+1} failed: {result.get('error', {}).get('message', 'Unknown error')}")
                    continue # انتقل للمفتاح التالي
        except Exception as e:
            logging.error(f"Error with Key {index+1}: {e}")
            continue
    return None # إذا فشلت كل المفاتيح

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user_message = update.message.text
    payload = {
        "contents": [{"parts": [{"text": f"{BASE_KNOWLEDGE}\n\nسؤال الزبون: {user_message}"}]}]
    }

    answer = await get_gemini_response(payload)
    
    if answer:
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text("المعذرة يا غالي، يبدو أن هناك ضغط كبير على الخدمة حالياً. جرب تراسلني بعد قليل.")

if __name__ == '__main__':
    # تشغيل سيرفر Flask للبقاء حياً على Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    # تشغيل البوت
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    print(f"--- البوت شغال بـ {len(API_KEYS)} مفاتيح تبديل ---")
    app.run_polling()