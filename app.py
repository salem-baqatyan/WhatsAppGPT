import logging
import httpx
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- الإعدادات ---
ID_INSTANCE = "7107612913" 
API_TOKEN_INSTANCE = "36c970442a274b7e8299857895b9a7e6ab2755bde987498abd"
WA_URL = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN_INSTANCE}"

API_KEYS = [
    "AIzaSyBmrSrN9oQ-zkb1vHdyz2HfpNCIppo6nsM",
    "AIzaSyACPCUdAxGvkJhA3LBGFHixWzduxY8cf88",
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
    """استخدام Client متزامن لتجنب مشاكل Flask async"""
    payload = {"contents": [{"parts": [{"text": f"{BASE_KNOWLEDGE}\n\nسؤال الزبون: {user_msg}"}]}]}
    for key in API_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            # استخدام الحظر (Sync) بدلاً من Async
            with httpx.Client() as client:
                res = client.post(url, json=payload, timeout=30.0)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except: continue
    return "المعذرة، واجهت مشكلة تقنية. جرب لاحقاً."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # تسجيل البيانات القادمة للفحص (اختياري)
    print(f"Incoming: {json.dumps(data)}") 

    try:
        # Green-API يرسل نوع الويب هوك في حقل typeWebhook
        if data.get("typeWebhook") == "incomingMessageReceived":
            chat_id = data["senderData"]["chatId"]
            
            # التأكد من وجود نص في الرسالة
            message_data = data.get("messageData", {})
            user_text = ""
            
            if "textMessageData" in message_data:
                user_text = message_data["textMessageData"].get("textMessage", "")
            
            if user_text:
                # الحصول على الرد
                ai_answer = get_gemini_response(user_text)
                
                # إرسال الرد عبر Green-API
                with httpx.Client() as client:
                    client.post(WA_URL, json={
                        "chatId": chat_id,
                        "message": ai_answer
                    })
    except Exception as e:
        print(f"Error in Webhook: {e}")
    
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return "WhatsApp Bot is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)