import os
import json
import logging
from flask import Flask, request, jsonify
import httpx
from functools import lru_cache
import time

app = Flask(__name__)

# --- إعداد الـ Logging الاحترافي لمراقبة السيرفر ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

# تحديد المجلد الرئيسي للمشروع بشكل مطلق لضمان قراءة المجلدات على لينكس (Render)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# قراءة الإعدادات من متغيرات البيئة في Render مع وجود قيم احتياطية
WAHA_BASE_HOST = os.environ.get("WAHA_BASE_HOST", "http://localhost")
WAHA_API_KEY = os.environ.get("WAHA_API_KEY", "dfe525d2894d40de971fdfe6b0b9adb2")

# حد أقصى لحجم ملفات المعرفة لكل شركة لتجنب انفجار الذاكرة (500 كيلوبايت)
MAX_KNOWLEDGE_SIZE_BYTES = 500 * 1024 

# ----------------------------
# 1. إضافة Cache للـ config
# ----------------------------
_config_cache = {}

def load_company_config(company_name):
    current_time = time.time()
    if company_name in _config_cache:
        cached_data, timestamp = _config_cache[company_name]
        if current_time - timestamp < 60:  # صلاحية الكاش 60 ثانية
            return cached_data

    # استخدام BASE_DIR لضمان المسار المطلق الصحيح سحابياً
    config_path = os.path.join(BASE_DIR, "companies", company_name, "config.json")
    config_data = {
        "company_name": company_name,
        "waha_port": 3000,
        "session": "default",
        "gemini_keys": [],
        "openrouter_api_key": "",
        "model": "gemini-2.5-flash",
        "openrouter_model": "google/gemini-2.5-flash",
        "temperature": 0.7
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                config_data.update(loaded_config)
                if "openrouter_model" not in config_data:
                    config_data["openrouter_model"] = f"google/{config_data['model']}" if "/" not in config_data['model'] else config_data['model']
    except Exception as e:
        logging.error(f"❌ فشل قراءة config.json للشركة {company_name}: {e}")
    
    _config_cache[company_name] = (config_data, current_time)
    return config_data

# ----------------------------
# 2. دالة قراءة قاعدة المعرفة مع الفلترة وحماية الذاكرة
# ----------------------------
def load_company_knowledge(company_name):
    data_path = os.path.join(BASE_DIR, "companies", company_name)
    if not os.path.exists(data_path):
        logging.warning(f"⚠️ المجلد المخصص للشركة [{company_name}] غير موجود.")
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
                logging.warning(f"⚠️ تجاوزت شركة [{company_name}] الحد الأقصى المسموح به لقاعدة المعرفة.")
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
                logging.error(f"⚠️ فشل قراءة الملف {file_name} للشركة {company_name}: {e}")
    except Exception as e:
        logging.error(f"❌ خطأ أثناء قراءة ملفات مجلد الشركة {company_name}: {e}")
            
    return content

# ----------------------------
# 3. دالة جلب الاستجابة من OpenRouter
# ----------------------------
def get_openrouter_response(user_msg, base_knowledge, openrouter_key, router_model, temperature):
    if not openrouter_key:
        logging.warning("⚠️ محاولة اتصال بـ OpenRouter ولكن المفتاح فارغ.")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": router_model,
        "messages": [{"role": "user", "content": f"{base_knowledge}\n\nسؤال الزبون: {user_msg}"}],
        "temperature": temperature
    }

    for attempt in range(2):
        try:
            logging.info(f"⚡ محاولة جلب الرد عبر OpenRouter (محاولة {attempt+1})...")
            with httpx.Client() as client:
                res = client.post(url, json=payload, headers=headers, timeout=30.0)
                if res.status_code == 200:
                    result = res.json()
                    return result["choices"][0]["message"]["content"]
                logging.error(f"❌ فشل اتصال OpenRouter بكود: {res.status_code}")
        except Exception as e:
            logging.error(f"❌ خطأ أثناء الاتصال بـ OpenRouter في المحاولة {attempt+1}: {e}")
        time.sleep(1)
    
    return None

# ----------------------------
# 4. محرك المعالجة الذكي
# ----------------------------
def get_intelligent_response(user_msg, base_knowledge, config):
    api_keys = config.get("gemini_keys", [])
    model_name = config.get("model", "gemini-2.5-flash")
    temperature = config.get("temperature", 0.7)
    openrouter_key = config.get("openrouter_api_key", "")
    router_model = config.get("openrouter_model")

    payload = {
        "contents": [{"parts": [{"text": f"{base_knowledge}\n\nسخدام الزبون: {user_msg}"}]}],
        "generationConfig": {"temperature": temperature}
    }

    last_error = None

    for key_index, key in enumerate(api_keys, start=1):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        
        for attempt in range(2): 
            try:
                with httpx.Client() as client:
                    res = client.post(url, json=payload, timeout=30.0)

                if res.status_code == 200:
                    result = res.json()
                    candidates = result.get("candidates", [])
                    if not candidates: continue
                    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                    if not content: continue
                    return content

                elif res.status_code == 429:
                    logging.warning(f"⚠️ المفتاح #{key_index}: حد طلبات (429). سيتم التبديل...")
                    last_error = "quota"
                    break
                else:
                    logging.error(f"⚠️ المفتاح #{key_index}: خطأ كود {res.status_code}")
                    last_error = "server"
                    break

            except (httpx.TimeoutException, httpx.ConnectError) as conn_err:
                logging.error(f"⚠️ المفتاح #{key_index}: خطأ اتصال/مهلة (المحاولة {attempt+1}): {conn_err}")
                last_error = "connection"
                time.sleep(1)

    logging.warning("⚠️ جميع قنوات Gemini مستهلكة أو معطلة. جاري التحويل الاحتياطي لـ OpenRouter...")
    openrouter_content = get_openrouter_response(user_msg, base_knowledge, openrouter_key, router_model, temperature)
    if openrouter_content:
        return openrouter_content

    if last_error == "quota":
        return "المعذرة، تم استهلاك الحصة الحالية، حاول مجدداً بعد قليل."
    if last_error == "connection":
        return "المعذرة، يوجد انقطاع مؤقت في الاتصال بخوادم المعالجة."
    return "المعذرة، واجهت مشكلة تقنية مؤقتة، يرجى المحاولة لاحقاً."

# ----------------------------
# 5. دالة إرسال الرسائل عبر WAHA السحابية (المحدثة لمتغيرات البيئة الديناميكية)
# ----------------------------
def send_waha_message(waha_port, session_name, chat_id, text, company_name):
    config = load_company_config(company_name)
    
    # 1. أولاً: نحاول قراءة الرابط من متغيرات البيئة في Render (بتحويل اسم الشركة لأحرف كبيرة)
    # مثلاً لو الشركة saas_bot سيبحث عن متغير باسم: WAHA_URL_SAAS_BOT
    env_var_name = f"WAHA_URL_{company_name.upper()}"
    waha_url_config = os.environ.get(env_var_name)
    
    # 2. ثانياً: إذا لم نجد متغير بيئة، نأخذ الرابط من ملف config.json الخاص بالشركة
    if not waha_url_config:
        waha_url_config = config.get("waha_url")
    
    # بناء الرابط النهائي للإرسال
    if waha_url_config:
        # إزالة السلاش المائل الأخير إن وجد لضمان عدم تكراره في الرابط
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

# ----------------------------
# 6. استقبال طلبات الـ Webhook
# ----------------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        logging.warning("⚠️ تم استقبال طلب ويب هوك بـ JSON فارغ أو غير صالح!")
        return jsonify({"error": "Invalid or missing JSON"}), 400

    if data.get("event") == "message":
        payload = data.get("payload", {})
        
        if payload.get("fromMe") is True:
            return "Ignored outward message", 200
            
        user_msg = payload.get("body", "")
        chat_id = payload.get("from", "")
        company_name = request.args.get("company_name")

        # الفحص الأمني السحابي المتوافق مع بيئة لينكس المطلقة
        if not company_name or not os.path.exists(os.path.join(BASE_DIR, "companies", company_name)):
            logging.error(f"❌ محاولة وصول غير مصرح بها أو شركة غير مسجلة: [{company_name}]")
            return jsonify({"error": "Unauthorized or unknown company"}), 403

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
    # قراءة المنفذ من Render تلقائياً
    port = int(os.environ.get("PORT", 8888))
    app.run(host='0.0.0.0', port=port, threaded=True)