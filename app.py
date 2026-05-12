import logging
import httpx
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- الإعدادات الجديدة لـ Meta ---
ACCESS_TOKEN = "EAANzMXXnzN8BRcOpZCrpEk3acDYvlJbs9gnVx7YvDRXXttUxUgANBSnHJVEGOXHYxXwneytyR47Cq0Xa7HFxIEHdEsxp6bmbD2XDF51F2lY2NrjAXkmmFLy05jLTB7pUHvHDJ7XcTBuF5Pp2ptOPnzkAnvolpg7P9pm64QDOeo8B343iuUxQWa3caXKFKlkU0c6RiMtwJh9itlLdm7nwbfwEh6KeGL0DdqhuZARRGCElR2i5wIBzqP7xZBUJrDOPUJg5F3PogPOb4M6Lb4rZBFzVsAZDZD" # Access Token من صفحة Meta
PHONE_NUMBER_ID = "1089127494288944" # معرف الرقم الذي حصلت عليه
VERIFY_TOKEN = "salem_secret_123" # اختر أي كلمة سر وضعها في واجهة Meta

META_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

API_KEYS = [
    "AIzaSyC9_Fj3IWp9cJdhRqKUUccQK7QQz1VGhgc",
    "AIzaSyC8DBpLcv408zfz3TmFDSTzoWcpSR8c6Dg",
]

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
    for index, key in enumerate(API_KEYS):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            with httpx.Client() as client:
                res = client.post(url, json=payload, timeout=30.0)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            continue
    return "المعذرة، واجهت مشكلة تقنية."

# --- التحقق من الـ Webhook (مهم لـ Meta) ---
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# --- معالجة الرسائل الواردة ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    try:
        # استخراج الرسالة من هيكلة Meta
        if "messages" in data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}):
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            chat_id = message["from"]
            
            if message.get("type") == "text":
                user_text = message["text"]["body"]
                ai_answer = get_gemini_response(user_text)

                # إرسال الرد عبر Meta API
                headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
                
                # فحص إذا كان الرد رابط صورة
                if "http" in ai_answer and any(ext in ai_answer for ext in [".jpg", ".png", ".jpeg"]):
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": chat_id,
                        "type": "image",
                        "image": {"link": ai_answer.strip(), "caption": "إليك الصورة المطلوبة"}
                    }
                else:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": chat_id,
                        "type": "text",
                        "text": {"body": ai_answer}
                    }

                with httpx.Client() as client:
                    client.post(META_URL, headers=headers, json=payload)

    except Exception as e:
        print(f"Error: {e}")
    
    return jsonify({"status": "success"}), 200

@app.route('/')
def home(): return "Meta WhatsApp Bot is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)