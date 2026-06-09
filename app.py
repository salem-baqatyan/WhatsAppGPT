import os
import json
import logging
from flask import Flask, request, jsonify
import httpx

app = Flask(__name__)

# --- إعدادات سياق السيرفر المحلي ---
WAHA_API_URL = "http://localhost:3000/api" 
# لم نعد بحاجة لتثبيت SESSION واحدة في الأعلى لأنها ستأتي ديناميكياً من الـ Webhook

# --- إعدادات Gemini ---
API_KEYS = [
    "AQ.Ab8RN6JZLzMbITgh3_CvDdKr0opJI_sc4ylMed70YEqJIe8YFg",
]

# دالة مطورة لقراءة بيانات الشركة ديناميكياً بناءً على اسم الجلسة
def load_company_data(session_name):
    data_path = os.path.join("companies", session_name)

    if not os.path.exists(data_path):
        print(f"⚠️ المجلد {session_name} غير موجود")
        return ""

    content = ""

    for file_name in os.listdir(data_path):
        file_path = os.path.join(data_path, file_name)

        # تجاهل المجلدات الفرعية
        if not os.path.isfile(file_path):
            continue

        try:
            if file_name.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content += "\n\n" + json.dumps(
                        json.load(f),
                        ensure_ascii=False,
                        indent=2
                    )

            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content += "\n\n" + f.read()

        except Exception as e:
            print(f"⚠️ فشل قراءة {file_name}: {e}")

    return content
def get_gemini_response(user_msg, base_knowledge):
    payload = {"contents": [{"parts": [{"text": f"{base_knowledge}\n\nسؤال الزبون: {user_msg}"}]}]}
    
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

# دالة الإرسال مع تمرير اسم الجلسة الصحيحة ديناميكياً لـ WAHA
def send_waha_message(session_name, chat_id, text):
    url = f"{WAHA_API_URL}/sendText"    
    
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": session_name # إرسال الرد عبر نفس الجلسة التي استقبلت الرسالة
    }
    
    headers = {
        "X-Api-Key": "d7ed3708aca64d96af708da7db06d5c9",
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client() as client:
            res = client.post(url, json=payload, headers=headers, timeout=10.0)
            if res.status_code in [200, 201]:
                print(f"✅ [{session_name}] تم إرسال الرد بنجاح إلى: {chat_id}")
                return True
            else:
                print(f"⚠️ [{session_name}] WAHA رفض الإرسال. كود الحالة: {res.status_code}")
                return False
    except Exception as e:
        print(f"❌ خطأ أثناء الإرسال عبر WAHA للجلسة {session_name}: {e}")
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
        
        # استخراج اسم الجلسة ديناميكياً من بيانات الويب هوك المرسلة من WAHA
        session_name = data.get("session", "default")

        if user_msg and chat_id:
            print(f"💬 [{session_name}] رسالة واردة من {chat_id}: {user_msg}")
            
            # 1. تحميل المعرفة الخاصة بهذه الشركة تحديداً في هذه اللحظة
            company_knowledge = load_company_data(session_name)
            
            # 2. توليد الرد بناءً على معرفة الشركة المستهدفة
            ai_answer = get_gemini_response(user_msg, company_knowledge)
            print(f"🤖 [{session_name}] رد الذكاء الاصطناعي الجاهز: {ai_answer}")
            
            # 3. إرسال الرد عبر الجلسة الصحيحة
            send_waha_message(session_name, chat_id, ai_answer)
            
            return "OK", 200

    return "Ignored event", 200

@app.route('/')
def home():
    return "Multi-Tenant WAHA AI Bot is Running Locally!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)