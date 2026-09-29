import datetime
import requests
import logging

# جلب سعر الذهب الحي والمباشر من الأسواق العالمية
def get_live_gold_price():
    try:
        response = requests.get("https://api.gold-api.com/price/XAU", timeout=8)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 4141.50))
    except Exception as e:
        logging.error(f"خطأ في الاتصال بسوق المال العالمي: {e}")
    return 4141.50

# التحقق من الاشتراك الإجباري في القناة الرسمية
async def check_forced_subscription(user_id, admin_id, channel_username, context):
    if user_id == admin_id:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"خطأ في التحقق من الاشتراك: {e}")
    return False

# التحقق من صلاحية رخصة المستخدم
def is_subscribed(user_id, admin_id, db):
    if user_id == admin_id:
        return True
    if user_id in db["users"]:
        expiry_date = db["users"][user_id].get("expiry")
        if expiry_date and datetime.datetime.now() < expiry_date:
            return True
    return False
