import requests
from openai import OpenAI
from groq import Groq

def check_groq(api_key):
    """فحص مفتاح Groq (يبدأ عادة بـ gsk_)"""
    try:
        client = Groq(api_key=api_key)
        # محاولة جلب قائمة النماذج لفحص الصلاحية
        client.models.list()
        return True, "Valid"
    except Exception as e:
        return False, str(e)

def check_openrouter(api_key):
    """فحص مفتاح OpenRouter (يبدأ عادة بـ sk-or-)"""
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True, "Valid"
        else:
            return False, f"Status Code: {response.status_code} - {response.text}"
    except Exception as e:
        return False, str(e)

def check_anthropic(api_key):
    """فحص مفتاح Anthropic / Claude (يبدأ عادة بـ sk-ant- أو AQ.)"""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    # نرسل طلب فارغ أو خاطئ عمداً لرؤية نوع الخطأ (إذا كان الخطأ بسبب المفتاح أم بسبب محتوى الطلب)
    try:
        response = requests.post(url, headers=headers, json={})
        # إذا كان المفتاح خاطئاً سيعيد الكود 401
        if response.status_code == 401:
            return False, "Invalid API Key"
        # إذا أعاد 400 (طلب سيئ بسبب نقص البيانات) فهذا يعني أن المفتاح تم قبوله وتجاوز مرحلة التحقق
        elif response.status_code == 400:
            return True, "Valid"
        else:
            return False, f"Status Code: {response.status_code}"
    except Exception as e:
        return False, str(e)

def check_openai(api_key):
    """فحص مفتاح OpenAI (يبدأ عادة بـ sk-proj- أو sk-)"""
    try:
        client = OpenAI(api_key=api_key)
        # محاولة جلب النماذج لفحص الصلاحية
        client.models.list()
        return True, "Valid"
    except Exception as e:
        return False, str(e)

def identify_and_check_key(api_key):
    """التعرف التلقائي على نوع المفتاح وفحصه"""
    api_key = api_key.strip()
    
    if api_key.startswith("gsk_"):
        print(f"🔄 Checking Groq Key...")
        return check_groq(api_key)
        
    elif api_key.startswith("sk-or-"):
        print(f"🔄 Checking OpenRouter Key...")
        return check_openrouter(api_key)
        
    elif api_key.startswith("sk-proj-") or (api_key.startswith("sk-") and len(api_key) > 40 and "ant" not in api_key):
        print(f"🔄 Checking OpenAI Key...")
        return check_openai(api_key)
        
    elif api_key.startswith("AQ.") or "ant" in api_key:
        print(f"🔄 Checking Anthropic Key...")
        return check_anthropic(api_key)
        
    else:
        # محاولة فحص عامة إذا لم يتطابق النمط تماماً
        print(f"❓ Unknown key format. Trying general Anthropic/OpenAI check...")
        return False, "Unknown provider format"

# --- تجربة الكود ---
if __name__ == "__main__":
    # ضع المفاتيح التي تريد فحصها هنا في القائمة
    test_keys = [
        "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",
        "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",
        "AQ.Ab8RN6IsAuiqYtiPoBHd0v-GSFSzq7DX2qNlkLa0JejkwYak4w",
        "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"
    ]

    print("=== AI API Key Validator ===")
    for key in test_keys:
        # عرض أول وآخر 6 أحرف فقط من المفتاح للأمان أثناء الطباعة
        masked_key = f"{key[:6]}...{key[-6:]}" if len(key) > 12 else key
        
        is_valid, message = identify_and_check_key(key)
        
        if is_valid:
            print(f"✅ Success | Key: {masked_key} is WORKING!\n")
        else:
            print(f"❌ Failed  | Key: {masked_key} is INVALID. Reason: {message}\n")