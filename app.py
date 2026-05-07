import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# إعدادات Gemini و Green-API
GEMINI_KEY = "AIzaSyD9LVu-Xl6H3vNIAzFkWgC4oJaMr33sKS4"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
ID_INSTANCE = "7107612913"
API_TOKEN = "36c970442a274b7e8299857895b9a7e6ab2755bde987498abd"

COMPANY_DATA = "أنت مساعد لشركة LT للجوالات في اليمن. أجب بلهجة يمنية."

@app.route('/')
def home():
    return "سيرفر شركة LT يعمل بنجاح!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("وصل إشعار جديد:", data.get('typeWebhook'))

    if data.get('typeWebhook') == 'incomingMessageReceived':
        chat_id = data['senderData']['chatId']
        # استخدام .get لتجنب الأخطاء إذا كانت الرسالة ليست نصاً
        message_data = data.get('messageData', {})
        text_data = message_data.get('textMessageData', {})
        user_message = text_data.get('textMessage', '')

        if user_message:
            print(f"رسالة من {chat_id}: {user_message}")
            
            # إرسال لـ Gemini
            full_prompt = f"{COMPANY_DATA}\nالعميل: {user_message}\nالرد:"
            payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
            
            try:
                res = requests.post(GEMINI_URL, json=payload)
                bot_reply = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                
                # إرسال للواتساب
                send_url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
                requests.post(send_url, json={"chatId": chat_id, "message": bot_reply})
            except Exception as e:
                print(f"Error: {e}")

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)