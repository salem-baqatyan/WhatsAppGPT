import logging
import httpx
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# إعداد السيرفر الوهمي لـ Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # Render يعطينا المنفذ تلقائياً عبر متغير PORT
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# الإعدادات (يفضل استخدام Environment Variables في Render)
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB08cGSOO_2CUYLF0oN0voTv2KY5ZZ8mKc")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8766269475:AAGF6XecWHqHWHPXW8LWYWOXHwG8tYwRTmg")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

def get_knowledge_base():
    try:
        with open("knowledge_base.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "شركة ال تي موبايل - اليمن."

SYSTEM_PROMPT = f"أنت مساعد عملاء شركة ال تي في اليمن. أجب بلهجة يمنية. معلوماتك: {get_knowledge_base()}"

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    payload = {"contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nالزبون: {user_message}"}]}]}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_URL, json=payload, timeout=60.0)
            result = response.json()
            if response.status_code == 200 and "candidates" in result:
                answer = result["candidates"][0]["content"]["parts"][0]["text"]
                await update.message.reply_text(answer)
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == '__main__':
    # تشغيل سيرفر Flask في Thread منفصل
    threading.Thread(target=run_flask, daemon=True).start()
    
    # تشغيل بوت التيليجرام
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    print("--- البوت شغال الآن على Render بموديل 2.5 ---")
    app.run_polling()