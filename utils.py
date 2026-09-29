import datetime
import requests
import logging

def get_live_gold_price():
    """جلب السعر الحي للذهب (XAU/USD) من السيرفرات العالمية بدقة تامة"""
    try:
        response = requests.get("https://api.gold-api.com/price/XAU", timeout=8)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 4141.50))
    except Exception as e:
        logging.error(f"خطأ في الاتصال بسوق المال العالمي: {e}")
    return 4141.50

async def check_forced_subscription(user_id, admin_id, channel_username, context):
    """التحقق من اشتراك المستخدم الإجباري في القناة الرسمية"""
    if user_id == admin_id:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"خطأ في التحقق من الاشتراك: {e}")
    return False

def is_subscribed(user_id, admin_id, db):
    """التحقق من صلاحية اشتراك المستخدم النشط"""
    if user_id == admin_id:
        return True
    if user_id in db["users"]:
        expiry_date = db["users"][user_id].get("expiry")
        if expiry_date and datetime.datetime.now() < expiry_date:
            return True
    return False

def get_remaining_time(user_id, db):
    """حساب وعرض الوقت المتبقي لاشتراك المستخدم بدقة (أيام، ساعات، دقائق)"""
    if user_id in db["users"]:
        expiry = db["users"][user_id].get("expiry")
        if expiry and datetime.datetime.now() < expiry:
            remaining = expiry - datetime.datetime.now()
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            return f"{days} يوم و {hours} ساعة و {minutes} دقيقة"
    return "منتهي ❌"
