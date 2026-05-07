import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- إعدادات Gemini ---
GEMINI_KEY = "AIzaSyD9LVu-Xl6H3vNIAzFkWgC4oJaMr33sKS4"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"

# --- إعدادات Green-API (ضع بياناتك هنا) ---
ID_INSTANCE = "7107612913"
API_TOKEN = "36c970442a274b7e8299857895b9a7e6ab2755bde987498abd"

COMPANY_DATA = """أنت مساعد لشركة LT للجوالات في اليمن. أجب بلهجة يمنية محببة.
جوالاتنا: LT P30 (150$) و LT Note 20 (220$). مراكزنا في صنعاء وعدن وتعز."""

def send_whatsapp_message(chat_id, text):
    """وظيفة لإرسال رد إلى واتساب العميل"""
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": text
    }
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    # هذا السطر مهم جداً لتجاوز صفحة الحماية الخاصة بـ localtunnel
    response = jsonify({"status": "received"})
    response.headers.add("Bypass-Tunnel-Reminder", "true")
    
    data = request.json
    
    # اطبع البيانات القادمة لنتأكد من وصولها في التيرمينال
    print("إشعار جديد وصل:", data.get('typeWebhook'))

    if data.get('typeWebhook') == 'incomingMessageReceived':
        chat_id = data['senderData']['chatId']
        user_message = data['messageData']['textMessageData']['textMessage']
        
        print(f"رسالة من {chat_id}: {user_message}")

        full_prompt = f"{COMPANY_DATA}\nالعميل: {user_message}\nالرد:"
        gemini_payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
        
        try:
            res = requests.post(GEMINI_URL, json=gemini_payload)
            bot_reply = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            send_whatsapp_message(chat_id, bot_reply)
        except Exception as e:
            print(f"خطأ في Gemini: {e}")

    return response, 200

if __name__ == '__main__':
    app.run()