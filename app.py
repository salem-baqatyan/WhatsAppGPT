import requests
import os
from flask import Flask, request

app = Flask(__name__)

# --- إعدادات Gemini ---
GEMINI_KEY = "AIzaSyD9LVu-Xl6H3vNIAzFkWgC4oJaMr33sKS4"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"

# --- إعدادات Ultramsg ---
ULTRA_INSTANCE = "instance173961"
ULTRA_TOKEN = "ujvi08oon64c4j9a"

COMPANY_DATA = "أنت مساعد لشركة LT للجوالات في اليمن. أجب بلهجة يمنية."

@app.route('/')
def home():
    return "سيرفر شركة LT يعمل بنجاح مع Ultramsg!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("وصلت بيانات خام:", data) # هذا السطر سيظهر لنا في Logs ريندر فوراً

    # Ultramsg ترسل مصفوفة أحداث، نأخذ الحدث الأول
    if isinstance(data, list):
        event = data[0]
    else:
        event = data

    user_message = event.get('body')
    chat_id = event.get('from')

    if user_message and chat_id:
        # إذا كانت الرسالة "صادرة" من البوت نفسه لا ترد عليها (لتجنب الحلقة المفرغة)
        if event.get('sentId'): 
            return "OK", 200
            
        print(f"جاري الرد على {chat_id}...")
        # ... باقي كود Gemini والإرسال كما هو ...        
        # 1. إرسال لـ Gemini
        full_prompt = f"{COMPANY_DATA}\nالعميل: {user_message}\nالرد:"
        payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
        
        try:
            res = requests.post(GEMINI_URL, json=payload)
            res_json = res.json()
            
            # التأكد من استلام رد من Gemini
            if "candidates" in res_json:
                bot_reply = res_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # 2. إرسال للواتساب عبر Ultramsg
                send_url = f"https://api.ultramsg.com/{ULTRA_INSTANCE}/messages/chat"
                send_payload = {
                    "token": ULTRA_TOKEN,
                    "to": chat_id,
                    "body": bot_reply
                }
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                whatsapp_res = requests.post(send_url, data=send_payload, headers=headers)
                print(f"رد Ultramsg النهائي: {whatsapp_res.status_code}")
            else:
                print("خطأ في رد Gemini:", res_json)
                
        except Exception as e:
            print(f"حدث خطأ أثناء المعالجة: {e}")

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)