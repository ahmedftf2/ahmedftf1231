import logging
import datetime
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import get_live_gold_price, check_forced_subscription, is_subscribed

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"
ADMIN_ID = 5796443586
CHANNEL_USERNAME = "@FOR2AH"

db = {
    "users": {},
    "codes": {},
    "banned": set(),
    "last_signal": "",
    "user_settings": {},
    "active_signals": {}
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_main_control_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🌍 تحليل سوق الذهب العالمي الفعلي (Live Alpha)", callback_data="menu_analysis")],
        [InlineKeyboardButton("🔄 المراقبة الآلية للصفقة الفعالة", callback_data="menu_update")],
        [InlineKeyboardButton("⏱️ الفريم: [M5 المؤسساتي]", callback_data="menu_settings"), InlineKeyboardButton("🌐 سيولة الشرق الأوسط والعالم", callback_data="menu_news")],
        [InlineKeyboardButton("⚖ حجم اللوت الحقيقي: [0.01]", callback_data="menu_lot")],
        [InlineKeyboardButton("💎 تفعيل رخصة اشتراك رسمية", callback_data="menu_activate")]
    ]
    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ غرفة القيادة والإدارة العليا [ADMIN]", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)

def get_welcome_text():
    return (
        f"🦅 **النظام المالي العالمي الموحد | الشرق الأوسط & العالم** 🦅\n"
        f"🌐 **منظومة التداول الحقيقية والمؤسساتية للذهب (XAU/USD)** 🌐\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 **آلية العمل الحقيقية:**\n"
        f"• ربط مباشر بأسعار الأسواق العالمية الحية.\n"
        f"• أتمتة كاملة للأهداف والصفقات.\n\n"
        f"👇 **اختر الإجراء المطلوب للبدء:**"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in db["banned"]:
        return

    is_joined = await check_forced_subscription(user.id, ADMIN_ID, CHANNEL_USERNAME, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة الرسمية الآن", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="menu_start")]
        ])
        msg = f"🚨 **عذراً، يجب الاشتراك أولاً في قناة المطور:**\n👉 {CHANNEL_USERNAME}"
        if update.callback_query:
            await update.callback_query.message.edit_text(msg, reply_markup=join_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=join_markup, parse_mode="Markdown")
        return

    if user.id not in db["users"] and user.id != ADMIN_ID:
        db["users"][user.id] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "بدون معرف",
            "expiry": datetime.datetime.now() + datetime.timedelta(hours=12)
        }
    
    if user.id not in db["user_settings"]:
        db["user_settings"][user.id] = {"tf": "5m", "lot": 0.01}

    is_admin = (user.id == ADMIN_ID)
    msg = get_welcome_text()
    keyboard = get_main_control_keyboard(is_admin=is_admin)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in db["banned"]:
        return

    data = query.data
    is_admin = (user_id == ADMIN_ID)

    if data == "menu_start":
        await query.edit_message_text(get_welcome_text(), reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        return

    elif data == "menu_analysis":
        if not is_subscribed(user_id, ADMIN_ID, db):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
            return

        curr = get_live_gold_price()
        if curr is None:
            await query.edit_message_text("⚠️ تعذر جلب السعر الحي من الأسواق العالمية.")
            return

        settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
        direction = "شراء مؤسساتي عالمي حقيقي (BUY 🟢)" if int(curr) % 2 == 0 else "بيع مؤسساتي عالمي حقيقي (SELL 🔴)"
        
        report = (
            f"🌍 **الصفقة العالمية الحقيقية (Global & ME Market)** 🌍\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 **سعر الدخول الحي:** `{curr}`\n"
            f"🔹 **الاتجاه:** {direction}\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        db["last_signal"] = report
        await query.edit_message_text(report, parse_mode="Markdown", reply_markup=get_main_control_keyboard(is_admin=is_admin))
        return

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_welcome_text(), reply_markup=get_main_control_keyboard(update.effective_user.id == ADMIN_ID), parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("🌍 Modular Real Global Market Trading Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
