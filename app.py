import os
import json
import logging
from flask import Flask, request, jsonify
import httpx

app = Flask(__name__)

# --- إعدادات WAHA السحابية الجديدة ---
# تم تعديل الرابط ليتصل بـ Hugging Face مباشرة بدلاً من السيرفر المحلي
WAHA_API_URL = "https://salem775-waha-server.hf.space/api" 
WAHA_SESSION = "default"  # اسم الجلسة الافتراضي في WAHA
WAHA_API_KEY = "389f56a2575f4eed9bc77fcb3531660f"
# --- إعدادات Gemini ---
API_KEYS = [
    "AIzaSyDEAQyAKon7HKZn3F1wHdBx5i3KiNi3j4w",
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
                    print(f"⚠️ Gemini Key Failed: {res.status_code} - Response: {res.text}")
        except Exception as e:
            print(f"❌ Error with Gemini Key: {e}")
            continue
            
    return "المعذرة، واجهت مشكلة تقنية. جرب لاحقاً."

# دالة لإرسال الرسائل عبر WAHA مع التوثيق الصحيح عبر X-Api-Key
def send_waha_message(chat_id, text):
    # الرابط الافتراضي الصحيح لـ WAHA الأساسي
    url = f"{WAHA_API_URL}/sendText"    
    
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": WAHA_SESSION
    }
    
    # التوثيق الصارم الذي يطلبه سيرفر WAHA Core لتجنب الـ 401
    headers = {
        "X-Api-Key": "389f56a2575f4eed9bc77fcb3531660f",
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
async def webhook(): # إضافة async هنا
    data = request.json

    if data and data.get("event") == "message":
        payload = data.get("payload", {})
        
        if payload.get("fromMe") is True:
            return "Ignored outward message", 200
            
        user_msg = payload.get("body", "")
        chat_id = payload.get("from", "")

        if user_msg and chat_id:
            print(f"💬 رسالة واردة من {chat_id}: {user_msg}")
            
            # جلب رد الذكاء الاصطناعي
            ai_answer = get_gemini_response(user_msg)
            print(f"🤖 رد الذكاء الاصطناعي الجاهز: {ai_answer}")
            
            # إرسال الرد
            send_waha_message(chat_id, ai_answer)
            
            return "OK", 200

    return "Ignored event", 200

@app.route('/')
def home():
    return "WAHA AI Bot is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)