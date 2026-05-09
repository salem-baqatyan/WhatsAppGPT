import requests

url = "http://127.0.0.1:5000/chat"
payload = {"message": "السلام عليكم، ايش عندكم جوالات جديدة؟"}

try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("رد البوت الذكي:")
        print(response.json().get('response'))
    else:
        print(f"خطأ من السيرفر: {response.text}")
except Exception as e:
    print(f"فشل الاتصال بالسيرفر: {e}")