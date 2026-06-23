import os
import json
import logging
from flask import Flask, request, jsonify
import httpx
import time

app = Flask(__name__)

# --- إعداد الـ Logging الاحترافي لمراقبة السيرفر ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

# تحديد المجلد الرئيسي للمشروع بشكل مطلق لضمان قراءة المجلدات على Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WAHA_BASE_HOST = "http://localhost"
WAHA_API_KEY = "dfe525d2894d40de971fdfe6b0b9adb2"

MAX_KNOWLEDGE_SIZE_BYTES = 500 * 1024 

_config_cache = {}

def load_company_config(company_name):
    current_time = time.time()
    if company_name in _config_cache:
        cached_data, timestamp = _config_cache[company_name]
        if current_time - timestamp < 60:
            return cached_data

    config_path = os.path.join(BASE_DIR, "companies", company_name, "config.json")
    config_data = {
        "company_name": company_name,
        "waha_port": 3000,
        "session": "default",
        "gemini_keys": [],
        "openrouter_api_key": "",
        "model": "gemini-2.5-flash",
        "openrouter_model": "gpt-4o-mini",
        "temperature": 0.7
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                config_data.update(loaded_config)
    except Exception as e:
        logging.error(f"❌ فشل قراءة config.json للشركة {company_name}: {e}")
    
    _config_cache[company_name] = (config_data, current_time)
    return config_data

def load_company_knowledge(company_name):
    data_path = os.path.join(BASE_DIR, "companies", company_name)
    if not os.path.exists(data_path):
        return ""

    content = ""
    total_size = 0
    allowed_extensions = ('.json', '.md', '.txt')

    try:
        for file_name in os.listdir(data_path):
            if file_name == "config.json" or not file_name.endswith(allowed_extensions):
                continue
                
            file_path = os.path.join(data_path, file_name)
            if not os.path.isfile(file_path):
                continue

            file_size = os.path.getsize(file_path)
            if total_size + file_size > MAX_KNOWLEDGE_SIZE_BYTES:
                break

            total_size += file_size

            try:
                if file_name.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content += f"\n\n--- بيانات ملف {file_name} ---\n"
                        content += json.dumps(json.load(f), ensure_ascii=False)
                elif file_name.endswith(('.txt', '.md')):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content += f"\n\n--- محتوى ملف {file_name} ---\n"
                        content += f.read()
            except Exception as e:
                logging.error(f"⚠️ فشل قراءة الملف {file_name}: {e}")
    except Exception as e:
        logging.error(f"❌ خطأ مجلد الشركة {company_name}: {e}")
            
    return content

# ----------------------------
# دالة جلب الاستجابة من شات جي بي تي مباشرة (حل قطعي ومستقر)
# ----------------------------
def get_openrouter_response(user_msg, base_knowledge, openrouter_key, router_model, temperature):
    # استخدام مفتاح شات جي بي تي المستقر مباشرة وتجنب مشاكل الـ JSON
    hardcoded_openai_key = "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"
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {hardcoded_openai_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": f"{base_knowledge}\n\nسؤال الزبون: {user_msg}"}],
        "temperature": temperature
    }

    for attempt in range(2):
        try:
            logging.info(f"⚡ محاولة جلب الرد مباشرة عبر OpenAI Chat GPT (محاولة {attempt+1})...")
            with httpx.Client() as client:
                res = client.post(url, json=payload, headers=headers, timeout=30.0)
                if res.status_code == 200:
                    result = res.json()
                    return result["choices"][0]["message"]["content"]
                logging.error(f"❌ فشل اتصال OpenAI بكود: {res.status_code} - الرد: {res.text}")
        except Exception as e:
            logging.error(f"❌ خطأ أثناء الاتصال بـ OpenAI: {e}")
        time.sleep(1)
    
    return None

def get_intelligent_response(user_msg, base_knowledge, config):
    # تخطي الجيميني المعطل حالياً والتوجه مباشرة للحل المستقر
    openrouter_key = config.get("openrouter_api_key", "")
    router_model = config.get("openrouter_model", "gpt-4o-mini")
    temperature = config.get("temperature", 0.7)

    logging.warning("⚠️ تحويل المسار مباشرة إلى المحرك المستقر لـ OpenAI...")
    openrouter_content = get_openrouter_response(user_msg, base_knowledge, openrouter_key, router_model, temperature)
    if openrouter_content:
        return openrouter_content

    return "المعذرة، واجهت مشكلة تقنية مؤقتة، يرجى المحاولة لاحقاً."

# ----------------------------
# دالة إرسال الرسائل المصححة لقراءة روابط الـ Web السحابية
# ----------------------------
def send_waha_message(waha_port, session_name, chat_id, text, company_name):
    config = load_company_config(company_name)
    waha_url_config = config.get("waha_url")
    
    if waha_url_config:
        waha_url_config = waha_url_config.rstrip('/')
        url = f"{waha_url_config}/api/sendText"
    else:
        url = f"{WAHA_BASE_HOST}:{waha_port}/api/sendText"
    
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": session_name
    }
    
    headers = {
        "X-Api-Key": WAHA_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client(trust_env=False) as client:
            res = client.post(url, json=payload, headers=headers, timeout=15.0)
            if res.status_code in [200, 201]:
                logging.info(f"✅ [{company_name}] تم إرسال الرد بنجاح للعميل {chat_id} عبر {url}")
                return True
            logging.error(f"⚠️ [{company_name}] WAHA رفض الإرسال بكود: {res.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ خطأ اتصال بـ WAHA للشركة [{company_name}] عبر الرابط {url}: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    if data.get("event") == "message":
        payload = data.get("payload", {})
        
        if payload.get("fromMe") is True:
            return "Ignored outward message", 200
            
        user_msg = payload.get("body", "")
        chat_id = payload.get("from", "")
        company_name = request.args.get("company_name")

        if not company_name or not os.path.exists(os.path.join(BASE_DIR, "companies", company_name)):
            logging.error(f"❌ شركة غير مسجلة أو مسار خاطئ: [{company_name}]")
            return jsonify({"error": "Unauthorized"}), 403

        if user_msg and chat_id:
            logging.info(f"💬 [{company_name}] رسالة واردة من {chat_id}: {user_msg}")
            
            config = load_company_config(company_name)
            company_knowledge = load_company_knowledge(company_name)
            
            ai_answer = get_intelligent_response(user_msg, company_knowledge, config)
            logging.info(f"🤖 [{company_name}] الرد المولد: {ai_answer}")
            
            waha_port = config.get("waha_port", 3000)
            session_name = config.get("session", "default")
            
            send_waha_message(waha_port, session_name, chat_id, ai_answer, company_name)
            
            return "OK", 200

    return "Ignored event", 200

@app.route('/')
def home():
    return "SaaS Engine Core - Secured & Optimized for Production!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8888))
    app.run(host='0.0.0.0', port=port, threaded=True)