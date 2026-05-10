import logging
import httpx
import os
import json
import threading # أضفنا هذا لتسريع الاستجابة
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- الإعدادات ---
ID_INSTANCE = "7107612913" 
API_TOKEN_INSTANCE = "36c970442a274b7e8299857895b9a7e6ab2755bde987498abd"
WA_URL = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN_INSTANCE}"

API_KEYS = [
    "AIzaSyDR189t8qPWoycqsgsv_4O1rPa-5y9z2mg",
    "AIzaSyDsG5lrf7LXZIojTV0A2Q_jAV41D9hecAE",
    "AIzaSyAC2SPvOZH3IYySBmuJKZ_T3UvD8HL--H4",
    "AIzaSyDAuBdAUQVeF-GXVglKWruLiuGwt3zyWzY",
    "AIzaSyDRwTEOtxPP-gXNCHAPyuKbTOHHCV0-KUU"
]

# دالة جلب البيانات (تبقيها كما هي)
def load_data():
    data_path = "data/"
    content = ""
    files = ['faq.md', 'policies.md', 'prompt.txt', 'company.json', 'products.json', 'services.json']
    for file_name in files:
        try:
            with open(os.path.join(data_path, file_name), 'r', encoding='utf-8') as f:
                content += json.dumps(json.load(f), ensure_ascii=False) if file_name.endswith('.json') else f.read()
        except: pass
    return content

BASE_KNOWLEDGE = load_data()

def get_gemini_response(user_msg):
    payload = {"contents": [{"parts": [{"text": f"{BASE_KNOWLEDGE}\n\nسؤال الزبون: {user_msg}"}]}]}
    for key in API_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            with httpx.Client() as client:
                res = client.post(url, json=payload, timeout=20.0) # تقليل التايم آوت لسرعة التبديل
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except: continue
    return "المعذرة، واجهت مشكلة تقنية."

def process_and_reply(chat_id, user_text):
    """هذه الدالة تعمل في الخلفية لعدم تعطيل الويب هوك"""
    ai_answer = get_gemini_response(user_text)
    try:
        with httpx.Client() as client:
            client.post(WA_URL, json={"chatId": chat_id, "message": ai_answer}, timeout=10.0)
    except Exception as e:
        print(f"Error sending reply: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # استلام الرسالة ومعالجتها في خيط (Thread) منفصل فوراً
    if data.get("typeWebhook") == "incomingMessageReceived":
        try:
            chat_id = data["senderData"]["chatId"]
            user_text = data.get("messageData", {}).get("textMessageData", {}).get("textMessage", "")
            
            if user_text:
                # تشغيل المعالجة في الخلفية والرد على GREEN-API فوراً بـ 200
                threading.Thread(target=process_and_reply, args=(chat_id, user_text)).start()
        except: pass
    
    return jsonify({"status": "received"}), 200

@app.route('/')
def home(): return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))