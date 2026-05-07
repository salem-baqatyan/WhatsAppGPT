import requests

url = "http://127.0.0.1:5000/chat"
data = {"message": "السلام عليكم، ايش أفضل جوال عندكم؟"}

try:
    response = requests.post(url, json=data)
    print("رد البوت الذكي:")
    print(response.json().get('response'))
except Exception as e:
    print(f"حدث خطأ أثناء الاتصال بالسيرفر: {e}")