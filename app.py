import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- إعدادات Gemini ---
GEMINI_KEY = "AIzaSyD9LVu-Xl6H3vNIAzFkWgC4oJaMr33sKS4"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"

# --- إعدادات Ultramsg الجديدة ---
ULTRA_INSTANCE = "instance173961"
ULTRA_TOKEN = "ujvi08oon64c4j9a"

COMPANY_DATA = "أنت مساعد لشركة LT للجوالات في اليمن. أجب بلهجة يمنية."

@app.route('/')
def home():
    return "سيرفر شركة LT يعمل بنجاح مع Ultramsg!"

@app.route('/webhook', methods=['POST'])
def webhook():
    # استلام البيانات من Ultramsg
    data = request.json
    
    # في Ultramsg، النص يكون داخل data['body'] والراسل في data['from']
    user_message = data.get('body')
    chat_id = data.get('from')

    if user_message and chat_id:
        print(f"رسالة من {chat_id}: {user_message}")
        
        # 1. إرسال لـ Gemini
        full_prompt = f"{COMPANY_DATA}\nالعميل: {user_message}\nالرد:"
        payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
        
        try:
            res = requests.post(GEMINI_URL, json=payload)
            bot_reply = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            # 2. إرسال للواتساب عبر Ultramsg
            send_url = f"https://api.ultramsg.com/{ULTRA_INSTANCE}/messages/chat"
            send_payload = {
                "token": ULTRA_TOKEN,
                "to": chat_id,
                "body": bot_reply
            }
            # Ultramsg يفضل x-www-form-urlencoded
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            whatsapp_res = requests.post(send_url, data=send_payload, headers=headers)
            
            print(f"رد Ultramsg: {whatsapp_res.status_code} - {whatsapp_res.text}")
            
        except Exception as e:
            print(f"Error: {e}")

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)