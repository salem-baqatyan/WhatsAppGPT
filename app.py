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

WAHA_BASE_HOST = "http://localhost"
WAHA_API_KEY = "dfe525d2894d40de971fdfe6b0b9adb2"  # تم تأجيلها بناءً على طلبك لوقت الرفع

# حد أقصى لحجم ملفات المعرفة لكل شركة لتجنب انفجار الذاكرة (500 كيلوبايت)
MAX_KNOWLEDGE_SIZE_BYTES = 500 * 1024 

# ----------------------------
# 1. إضافة Cache للـ config (التحسين #1)
# لقراءة الإعدادات بسرعة من الذاكرة وتحديثها تلقائياً كل 60 ثانية
# ----------------------------
_config_cache = {}

def load_company_config(company_name):
    current_time = time.time()
    # إذا كانت الإعدادات موجودة في الكاش ولم تمر عليها دقيقة، نرجعها فوراً
    if company_name in _config_cache:
        cached_data, timestamp = _config_cache[company_name]
        if current_time - timestamp < 60:  # صلاحية الكاش 60 ثانية
            return cached_data

    config_path = os.path.join("companies", company_name, "config.json")
    config_data = {
        "company_name": company_name,
        "waha_port": 3000,
        "session": "default",
        "gemini_keys": [],
        "openrouter_api_key": "",
        "model": "gemini-2.5-flash",
        "openrouter_model": "google/gemini-2.5-flash", # معالجة ذكية لموديل OpenRouter
        "temperature": 0.7
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                config_data.update(loaded_config)
                # ضمان وجود مفتاح موديل أوبر تروتر احتياطاً
                if "openrouter_model" not in config_data:
                    config_data["openrouter_model"] = f"google/{config_data['model']}" if "/" not in config_data['model'] else config_data['model']
    except Exception as e:
        logging.error(f"❌ فشل قراءة config.json للشركة {company_name}: {e}")
    
    # حفظ في الكاش مع التوقيت الحالي
    _config_cache[company_name] = (config_data, current_time)
    return config_data

# ----------------------------
# 2. دالة قراءة قاعدة المعرفة مع الفلترة وحماية الذاكرة (المشكلة #3 و #4)
# ----------------------------
def load_company_knowledge(company_name):
    data_path = os.path.join("companies", company_name)
    if not os.path.exists(data_path):
        logging.warning(f"⚠️ المجلد المخصص للشركة [{company_name}] غير موجود.")
        return ""

    content = ""
    total_size = 0
    allowed_extensions = ('.json', '.md', '.txt')

    try:
        for file_name in os.listdir(data_path):
            # استثناء المجلدات، ملف الإعدادات، والملفات غير المدعومة
            if file_name == "config.json" or not file_name.endswith(allowed_extensions):
                continue
                
            file_path = os.path.join(data_path, file_name)
            if not os.path.isfile(file_path):
                continue

            # فحص حجم الملف قبل قراءته لحماية الـ RAM من الانفجار
            file_size = os.path.getsize(file_path)
            if total_size + file_size > MAX_KNOWLEDGE_SIZE_BYTES:
                logging.warning(f"⚠️ تجاوزت شركة [{company_name}] الحد الأقصى المسموح به لقاعدة المعرفة. تم إيقاف القراءة لحماية السيرفر.")
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
# 3. دالة جلب الاستجابة من OpenRouter (المشكلة #5 مصلحة عبر الـ config)
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
        "messages": [
            {
                "role": "user",
                "content": f"{base_knowledge}\n\nسؤال الزبون: {user_msg}"
            }
        ],
        "temperature": temperature
    }

    # إضافة نظام إعادة المحاولة لـ OpenRouter لضمان الاستقرار (المشكلة #8)
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
# 4. محرك المعالجة الذكي (مع إعادة المحاولة التلقائية عند الـ Timeouts)
# ----------------------------
def get_intelligent_response(user_msg, base_knowledge, config):
    api_keys = config.get("gemini_keys", [])
    model_name = config.get("model", "gemini-2.5-flash")
    temperature = config.get("temperature", 0.7)
    openrouter_key = config.get("openrouter_api_key", "")
    router_model = config.get("openrouter_model")

    payload = {
        "contents": [{"parts": [{"text": f"{base_knowledge}\n\nسؤال الزبون: {user_msg}"}]}],
        "generationConfig": {"temperature": temperature}
    }

    last_error = None

    for key_index, key in enumerate(api_keys, start=1):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        
        # نظام الـ Retry المضاف لمواجهة مشاكل الشبكة والـ Timeout (المشكلة #8)
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
                    logging.warning(f"⚠️ المفتاح #{key_index}: حد طلبات (429). سيتم التبديل للمفتاح التالي...")
                    last_error = "quota"
                    break # اخرج من حلقة الـ Retry وانتقل للمفتاح التالي فوراً
                else:
                    logging.error(f"⚠️ المفتاح #{key_index}: خطأ كود {res.status_code}")
                    last_error = "server"
                    break

            except (httpx.TimeoutException, httpx.ConnectError) as conn_err:
                logging.error(f"⚠️ المفتاح #{key_index}: خطأ اتصال/مهلة (المحاولة {attempt+1}): {conn_err}")
                last_error = "connection"
                time.sleep(1) # انتظر ثانية قبل إعادة المحاولة للشبكة

    # خطة الدفاع الأخيرة: تحويل لـ OpenRouter
    logging.warning("⚠️ جميع قنوات Gemini مستهلكة أو معطلة. جاري التحويل الاحتياطي لـ OpenRouter...")
    openrouter_content = get_openrouter_response(user_msg, base_knowledge, openrouter_key, router_model, temperature)
    if openrouter_content:
        return openrouter_content

    # الردود الثابتة والآمنة للمستخدم عند انقطاع كل الحلول العقلية
    if last_error == "quota":
        return "المعذرة، تم استهلاك الحصة الحالية، حاول مجدداً بعد قليل."
    if last_error == "connection":
        return "المعذرة، يوجد انقطاع مؤقت في الاتصال بخوادم المعالجة."
    return "المعذرة، واجهت مشكلة تقنية مؤقتة، يرجى المحاولة لاحقاً."

# ----------------------------
# 5. دالة إرسال الرسائل عبر WAHA (المشكلة #7 مصلحة عبر الـ config)
# ----------------------------
def send_waha_message(waha_port, session_name, chat_id, text, company_name):
    url = f"{WAHA_BASE_HOST}:{waha_port}/api/sendText"
    
    payload = {
        "chatId": chat_id,
        "text": text,
        "session": session_name  # تقرأ "session" من الـ config لتجهيز الـ Multi-session مستقبلاً بسلاسة
    }
    
    headers = {
        "X-Api-Key": WAHA_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client() as client:
            res = client.post(url, json=payload, headers=headers, timeout=15.0)
            if res.status_code in [200, 201]:
                logging.info(f"✅ [{company_name} - Port {waha_port}] تم إرسال الرد بنجاح للعميل {chat_id}")
                return True
            logging.error(f"⚠️ [{company_name}] WAHA رفض الإرسال بكود: {res.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ خطأ اتصال بـ WAHA للشركة [{company_name}] عبر منفذ {waha_port}: {e}")
        return False

# ----------------------------
# 6. استقبال وتأمين طلبات الـ Webhook (المشكلة #1 و #6)
# ----------------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        logging.warning("⚠️ تم استقبال طلب ويب هوك بـ JSON فارغ أو غير صالح!")
        return jsonify({"error": "Invalid or missing JSON"}), 400

    if data.get("event") == "message":
        payload = data.get("payload", {})
        
        # 1. تجاهل الرسائل الصادرة من البوت نفسه
        if payload.get("fromMe") is True:
            return "Ignored outward message", 200
            
        chat_id = payload.get("from", "")
        user_msg = payload.get("body", "")
        
        # 2. حماية صارمة: تجاهل الحالات (Statuses) والقصص تماماً
        # WAHA يرسل معرف الحالة غالباً على شكل يحتوي على 'status' أو 'broadcast'
        if "status" in chat_id.lower() or "broadcast" in chat_id.lower():
            logging.info(f"🚫 تم تجاهل رسالة من حالة/ستوري أو بث: {chat_id}")
            return "Ignored status/broadcast", 200

        # 3. حماية صارمة: تجاهل المجموعات (Groups) والقنوات
        # في واتساب، معرفات المجموعات تنتهي بـ @g.us
        # وأي رسالة من مجموعة تحتوي عادةً على حقل 'participant' (الشخص الذي أرسل داخل المجموعة)
        if chat_id.endswith("@g.us") or "participant" in payload:
            logging.info(f"🚫 تم تجاهل رسالة مجموعة (Group): {chat_id}")
            return "Ignored group message", 200

        # 4. التأكد أن المحادثة خاصة فقط (تنتهي بـ @c.us أو @s.whatsapp.net)
        if not (chat_id.endswith("@c.us") or chat_id.endswith("@s.whatsapp.net")):
            logging.info(f"🚫 تم تجاهل نوع محادثة غير مدعوم: {chat_id}")
            return "Ignored unsupported chat type", 200

        company_name = request.args.get("company_name")

        # التحقق من هوية الشركة لحماية الـ Webhook
        if not company_name or not os.path.exists(os.path.join("companies", company_name)):
            logging.error(f"❌ محاولة وصول غير مصرح بها أو شركة غير مسجلة: [{company_name}]")
            return jsonify({"error": "Unauthorized or unknown company"}), 403

        if user_msg and chat_id:
            logging.info(f"💬 [{company_name}] رسالة خاصة واردة من {chat_id}: {user_msg}")
            
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