import os
import logging
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, Application

# إعداد flask
app = Flask(__name__)

# إعدادات المفاتيح
API_KEY = "AIzaSyBm-sbcCSldhQhs0jBPguEMBEHCE0tuq4E"
TELEGRAM_TOKEN = "8766269475:AAGF6XecWHqHWHPXW8LWYWOXHwG8tYwRTmg"
# استخدام الرابط المحدث لضمان العثور على الموديل
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"

# إعداد تطبيق تيليجرام
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

def get_knowledge_base():
    try:
        with open("knowledge_base.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "شركة ال تي للجوالات - اليمن."

KNOWLEDGE_DATA = get_knowledge_base()
SYSTEM_PROMPT = f"أنت مساعد ذكي لشركة ال تي (LT Mobile) باليمن. معلوماتك: {KNOWLEDGE_DATA}. أجب بلهجة يمنية."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    payload = {"contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nسؤال العميل: {user_message}"}]}]}
    
    try:
        response = requests.post(GEMINI_URL, json=payload)
        data = response.json()
        if "candidates" in data:
            bot_text = data["candidates"][0]["content"]["parts"][0]["text"]
            await update.message.reply_text(bot_text)
    except Exception as e:
        logging.error(f"Error: {e}")

# إضافة المعالج
telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.update_queue.put(update)
        return "OK", 200

@app.route('/')
def index():
    return "Bot is Running", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)