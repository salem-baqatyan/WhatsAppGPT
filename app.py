import logging
import httpx
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- الإعدادات ---
# بيانات واتساب (مثال لمزود Green-API)
ID_INSTANCE = "7107612913" 
API_TOKEN_INSTANCE = "36c970442a274b7e8299857895b9a7e6ab2755bde987498abd"
WA_URL = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN_INSTANCE}"

# مفاتيح Gemini (نفس ميزة التدوير التي صممناها)
API_KEYS = [
    "AIzaSyDR189t8qPWoycqsgsv_4O1rPa-5y9z2mg",
    "AIzaSyDsG5lrf7LXZIojTV0A2Q_jAV41D9hecAE",
    "AIzaSyAC2SPvOZH3IYySBmuJKZ_T3UvD8HL--H4",
    "AIzaSyDAuBdAUQVeF-GXVglKWruLiuGwt3zyWzY",
    "AIzaSyDRwTEOtxPP-gXNCHAPyuKbTOHHCV0-KUU"
]

# --- دالة جلب البيانات (نفسها بدون تغيير) ---
def load_data():
    data_path = "data/"
    content = ""
    for file_name in ['faq.md', 'policies.md', 'prompt.txt', 'company.json', 'products.json', 'services.json']:
        try:
            with open(os.path.join(data_path, file_name), 'r', encoding='utf-8') as f:
                if file_name.endswith('.json'):
                    content += json.dumps(json.load(f), ensure_ascii=False)
                else:
                    content += f.read()
        except: pass
    return content

BASE_KNOWLEDGE = load_data()

async def get_gemini_response(user_msg):
    payload = {"contents": [{"parts": [{"text": f"{BASE_KNOWLEDGE}\n\nسؤال الزبون: {user_msg}"}]}]}
    for key in API_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=payload, timeout=30.0)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except: continue
    return "المعذرة، واجهت مشكلة تقنية. جرب لاحقاً."

# --- المسار (Webhook) الذي سيستقبل رسائل واتساب ---
@app.route('/webhook', methods=['POST'])
async def webhook():
    data = request.json
    try:
        # استخراج الرسالة ورقم المرسل (يختلف التنسيق حسب المزود)
        if data.get("typeWebhook") == "incomingMessageReceived":
            chat_id = data["senderData"]["chatId"]
            user_text = data["messageData"]["textMessageData"]["textMessage"]
            
            # الحصول على رد الذكاء الاصطناعي
            ai_answer = await get_gemini_response(user_text)
            
            # إرسال الرد إلى واتساب
            async with httpx.AsyncClient() as client:
                await client.post(WA_URL, json={
                    "chatId": chat_id,
                    "message": ai_answer
                })
    except Exception as e:
        print(f"Error: {e}")
    
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)