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
                else:
                    # هذا السطر سيطبع لك السبب الحقيقي في سجلات ريندر
                    error_detail = res.json().get('error', {}).get('message', 'Unknown Error')
                    print(f"⚠️ Key {index+1} Failed: {res.status_code} - {error_detail}")
                    
        except Exception as e:
            print(f"❌ Connection Error with Key {index+1}: {e}")
            continue
            
    return "المعذرة، واجهت مشكلة تقنية. جرب لاحقاً."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    try:
        # 1. فلترة: لا تعالج إلا الرسائل النصية الواردة فقط
        if data.get("typeWebhook") == "incomingMessageReceived":
            message_data = data.get("messageData", {})
            
            # التأكد أن الرسالة نصية وليست حالة (Status) أو إشعار آخر
            if message_data.get("typeMessage") == "textMessage":
                chat_id = data["senderData"]["chatId"]
                user_text = message_data["textMessageData"].get("textMessage", "")

                if user_text:
                    # الآن فقط نستهلك حصة Gemini
                    ai_answer = get_gemini_response(user_text)
                    
                    with httpx.Client() as client:
                        client.post(WA_URL, json={
                            "chatId": chat_id,
                            "message": ai_answer
                        })
        
        # تجاهل أي نوع آخر من الـ Webhooks (مثل Status أو Outgoing)
        else:
            # print(f"Ignored Webhook Type: {data.get('typeWebhook')}")
            pass

    except Exception as e:
        print(f"Error in Webhook: {e}")
    
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return "WhatsApp Bot is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)