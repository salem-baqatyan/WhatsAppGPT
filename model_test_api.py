import requests

API_KEY = "AIzaSyB9og33iRBLhrw0QCzr_HlthkkHeMx2m9M"

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(url)

    print("Status Code:", response.status_code)
    print("-" * 50)

    data = response.json()

    if response.status_code != 200:
        print("ERROR:")
        print(data)
        exit()

    models = data.get("models", [])

    if not models:
        print("لا توجد موديلات متاحة")
        exit()

    print(f"تم العثور على {len(models)} موديل:\n")

    for model in models:

        name = model.get("name", "UNKNOWN")
        display = model.get("displayName", "NO NAME")
        methods = model.get("supportedGenerationMethods", [])

        print("=" * 60)
        print("الاسم:", name)
        print("العرض:", display)
        print("العمليات:", methods)

except Exception as e:
    print("ERROR:", e)



