import requests
from concurrent.futures import ThreadPoolExecutor

API_KEYS = [
    "AIzaSyDQXj7pFrPuhn8Y2yqfOtZcodmBv1MmrLw",
    "AIzaSyDe8isbzz27N9Hxq656XQ-kzpvuk9FYHkg",
    "AIzaSyD7JyieDzcMXVcZQBh3m3TtV14uWCE97_k",
    "AIzaSyAaVjbXWvWzmQOI8Pg84Y4Fihr1o7VGyOg",
    "AIzaSyC4uELaP6Gi8NYD-ABn0EDSPlVkmC_DAq0",
]

def test_key(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print(f"🟢 VALID  : {api_key}")
        else:
            print(f"❌ INVALID: {api_key} | STATUS {response.status_code}")

    except Exception as e:
        print(f"❌ ERROR  : {api_key} | {e}")

print("\nجارِ اختبار المفاتيح...\n")

# تشغيل جميع الطلبات بنفس الوقت
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(test_key, API_KEYS)

print("\nانتهى الفحص.")