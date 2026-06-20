import httpx
import time

# إعدادات السيرفر السحابي
WAHA_API_URL = "https://salem775-waha-server.hf.space/api"
WAHA_API_KEY = "389f56a2575f4eed9bc77fcb3531660f"
RENDER_WEBHOOK_URL = "https://whatsappgpt-2dk9.onrender.com/webhook"

headers = {
    "X-Api-Key": WAHA_API_KEY,
    "Content-Type": "application/json"
}

def setup_waha():
    with httpx.Client() as client:
        # 1. إيقاف الجلسة الحالية أولاً لضمان قبول الإعدادات الجديدة
        print("🔄 محاولة إيقاف الجلسة لبرمجتها...")
        client.post(f"{WAHA_API_URL}/sessions/default/stop", headers=headers)
        time.sleep(2) # انتظار بسيط

        # 2. تشغيل الجلسة مع إعدادات الويب هوك كاملة
        print("🚀 بدء تشغيل الجلسة مع رابط الويب هوك السحابي...")
        payload = {
            "name": "default",
            "config": {
                "webhooks": [
                    {
                        "url": RENDER_WEBHOOK_URL,
                        "events": ["message"],
                        "hmac": None
                    }
                ]
            }
        }
        
        res = client.post(f"{WAHA_API_URL}/sessions/default/start", json=payload, headers=headers, timeout=20.0)
        
        if res.status_code in [200, 201]:
            print("✅ تـم الـربط بنجاح!")
            print("الآن أي رسالة تصل للرقم سيتم تحويلها تلقائياً إلى ريندير.")
        else:
            print(f"❌ فشل البدء. الحالة: {res.status_code}")
            print(f"الرد: {res.text}")

if __name__ == "__main__":
    setup_waha()