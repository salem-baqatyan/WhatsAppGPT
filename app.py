import os
import json
import logging
from flask import Flask, request, jsonify
import httpx
import asyncio

app = Flask(__name__)

# --- إعدادات WAHA السحابية الجديدة ---
WAHA_API_URL = "https://salem775-waha-server.hf.space/api" 
WAHA_SESSION = "default"  
WAHA_API_KEY = "c9aafb85e61b461ca721235673559c04"

# --- إعدادات Gemini ---
API_KEYS = [
    "AIzaSyDEAQyAKon7HKZn3F1wHdBx5i3KiNi3j4w",
]

# --- تحميل قاعدة البيانات مرة واحدة فقط عند تشغيل السيرفر لتسريع الاستجابة ---
def load_data():
    data_path = "data/"
    content = ""
    files = ['faq.md', 'policies.md', 'prompt.txt', 'company.json', 'products.json', 'services.json']
    for file_name in files:
        try:
            with open(os.path.join(data_path, file_name), 'r', encoding='utf-8') as f:
                if file_name.endswith('.json'):
                    content += json.dumps(json.load(f), ensure_ascii=False)
                else:
                    content += f.read()
        except: pass
    return content

BASE_KNOWLEDGE = load_data()

# دالة غير متزامنة لجلب رد Gemini دون تعطيل السيرفر
async def get_gemini_response_async(user_msg):
    payload = {"contents": [{"parts": [{"text": f"{BASE_KNOWLEDGE}\n\nسؤال الزبون: {user_msg}"}]}]}
    
    for index, key in enumerate(API_KEYS):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=payload, timeout=30.0)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    print(f"⚠️ Gemini Key {index} Failed: {res.status_code}.")
                    continue
        except Exception as e:
            print(f"❌ Error with Gemini Key {index}: {e}")
            continue
            
    return "المعذرة، واجهت مشكلة تقنية مؤقتة لكثرة الطلبات. يرجى المحاولة بعد قليل."

# دالة غير متزامنة لإرسال الرسائل عبر WAHA
async def send_waha_message_async(chat_id, text):
    url = f"{WAHA_API_URL}/sendText"    
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": WAHA_SESSION
    }
    headers = {
        "X-Api-Key": WAHA_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if res.status_code in [200, 201]:
                print(f"✅ ممتاز! تم إرسال الرد بنجاح إلى العميل: {chat_id}")
                return True
            else:
                print(f"⚠️ WAHA رفض الإرسال. كود الحالة: {res.status_code}")
                return False
    except Exception as e:
        print(f"❌ خطأ أثناء الإرسال عبر WAHA: {e}")
        return False

# دالة وسيطة لمعالجة مهمة الذكاء الاصطناعي والإرسال في الخلفية منفصلة تماماً
async def process_bot_reply(chat_id, user_msg):
    print(f"💬 بدأت معالجة رسالة العميل {chat_id}: {user_msg}")
    ai_answer = await get_gemini_response_async(user_msg)
    print(f"🤖 رد الذكاء الاصطناعي الجاهز: {ai_answer}")
    await send_waha_message_async(chat_id, ai_answer)

@app.route('/webhook', methods=['POST'])
def webhook(): 
    data = request.json

    if data and data.get("event") == "message":
        payload = data.get("payload", {})
        
        if payload.get("fromMe") is True:
            return "Ignored outward message", 200
            
        user_msg = payload.get("body", "")
        chat_id = payload.get("from", "")

        if user_msg and chat_id:
            # هنا السحر: نطلق دالة المعالجة في الخلفية عبر حلقة الأحداث (Event Loop) دون جعل WAHA ينتظر ثانية واحدة!
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            loop.create_task(process_bot_reply(chat_id, user_msg))
            
            # نرد فوراً بـ OK لـ WAHA لإبقاء الاتصال مستقراً وخفيفاً
            return "OK", 200

    return "Ignored event", 200

@app.route('/')
def home():
    return "WAHA AI Bot is Running 24/7!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)