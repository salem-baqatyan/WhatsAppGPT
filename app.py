import os
import json
import logging
from flask import Flask, request, jsonify
import httpx
import threading
import time

app = Flask(__name__)

# --- إعدادات WAHA السحابية الجديدة ---
WAHA_API_URL = "https://salem775-waha-server.hf.space/api" 
WAHA_SESSION = "default"  
WAHA_API_KEY = "389f56a2575f4eed9bc77fcb3531660f"

# --- إعدادات Gemini (يمكنك إضافة مصفوفة مفاتيحك التجريبية هنا) ---
API_KEYS = [
    "AIzaSyDEAQyAKon7HKZn3F1wHdBx5i3KiNi3j4w",
    # "ضع_المفتاح_التجريبي_الثاني_هنا",
    # "ضع_المفتاح_التجريبي_الثالث_هنا",
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

def get_gemini_response(user_msg):
    payload = {"contents": [{"parts": [{"text": f"{BASE_KNOWLEDGE}\n\nسؤال الزبون: {user_msg}"}]}]}
    
    # المرور على المفاتيح بالتناوب في حال فشل أحدها أو وصل للحد الأقصى
    for index, key in enumerate(API_KEYS):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            with httpx.Client() as client:
                res = client.post(url, json=payload, timeout=30.0)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    # إذا قوقل أرجعت خطأ 429 (ضغط) أو أي خطأ آخر، سيتم الانتقال تلقائياً للمفتاح التالي
                    print(f"⚠️ Gemini Key {index} Failed: {res.status_code}. Trying next key...")
                    continue
        except Exception as e:
            print(f"❌ Error with Gemini Key {index}: {e}")
            continue
            
    return "المعذرة، واجهت مشكلة تقنية مؤقتة لكثرة الطلبات. يرجى المحاولة بعد قليل."

# دالة لإرسال الرسائل عبر WAHA
def send_waha_message(chat_id, text):
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
        with httpx.Client() as client:
            res = client.post(url, json=payload, headers=headers, timeout=10.0)
            if res.status_code in [200, 201]:
                print(f"✅ ممتاز! تم إرسال الرد بنجاح إلى العميل: {chat_id}")
                return True
            else:
                print(f"⚠️ WAHA رفض الإرسال. كود الحالة: {res.status_code}، الرد: {res.text}")
                return False
    except Exception as e:
        print(f"❌ خطأ أثناء الإرسال عبر WAHA: {e}")
        return False

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
            print(f"💬 رسالة واردة من {chat_id}: {user_msg}")
            
            ai_answer = get_gemini_response(user_msg)
            print(f"🤖 رد الذكاء الاصطناعي الجاهز: {ai_answer}")
            
            send_waha_message(chat_id, ai_answer)
            
            return "OK", 200

    return "Ignored event", 200

@app.route('/')
def home():
    return "WAHA AI Bot is Running 24/7!"

# --- وظيفة منع النوم الذاتية (Keep Alive) ---
def keep_alive():
    # ننتظر 20 ثانية حتى يتأكد تشغيل السيرفر بالكامل أول مرة
    time.sleep(20)
    while True:
        try:
            # السيرفر ينادي رابط الهوم الخاص به ورابط سيرفر WAHA ليمنعهما من النوم
            with httpx.Client() as client:
                client.get("https://whatsappgpt-2dk9.onrender.com/", timeout=10.0)
                client.get("https://salem775-waha-server.hf.space/", timeout=10.0)
            print("⏰ [Ping] تم إنعاش السيرفرات بنجاح لضمان استمرار العمل 24 ساعة.")
        except Exception as e:
            print(f"⚠️ [Ping Error]: {e}")
        # تكرار العملية كل 10 دقائق (600 ثانية)
        time.sleep(600)

if __name__ == '__main__':
    # تشغيل نظام منع النوم في خلفية السيرفر (Thread منفصل) دون التأثير على استقبال الرسائل
    threading.Thread(target=keep_alive, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)