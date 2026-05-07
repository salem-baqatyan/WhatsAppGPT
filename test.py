import requests

# رابط السيرفر الخاص بك على ريندر
url = "https://whatsappgpt-2dk9.onrender.com/webhook"

# بيانات وهمية كأنها قادمة من واتساب
payload = {
    "typeWebhook": "incomingMessageReceived",
    "senderData": {"chatId": "967775445127@c.us"},
    "messageData": {
        "textMessageData": {"textMessage": "هلا، بكم الجوال الـ P30؟"}
    }
}

print("جاري فحص السيرفر...")
response = requests.post(url, json=payload)
print(f"الحالة: {response.status_code}")
print(f"الرد: {response.text}")