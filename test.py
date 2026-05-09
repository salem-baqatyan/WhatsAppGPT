import requests

API_KEY = "AIzaSyB08cGSOO_2CUYLF0oN0voTv2KY5ZZ8mKc"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

response = requests.get(url)
models = response.json()

if 'models' in models:
    print("--- الموديلات المتاحة لحسابك هي: ---")
    for m in models['models']:
        print(m['name'])
else:
    print("فشل في جلب الموديلات، تأكد من المفتاح:")
    print(models)