import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from utils import init_db, analyze_market_signal

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"
ADMIN_IDS = [5796443586]

init_db()

def check_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def check_vip(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    try:
        conn = sqlite3.connect("bot_database.db", timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT expiry FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False
        expiry_date = datetime.fromisoformat(row[0])
        if expiry_date > datetime.now():
            return True
    except Exception:
        pass
    return False

WELCOME_MESSAGE = (
    "🦅 محلل اسواق المال الفوركس احمد السيد 🦅\n"
    "💎 بوت احمد السيد الاحترافي للذهب والثغرات 💎\n"
    "👑━━━━━━━━━━━━━━━━━━━━👑\n"
    "البوت مخصص لتحليل الذهب vip💲🦅\n"
    "📞 للدعم و تفعيل البوت : @V8V8VN\n\n"
    "👇 اختر من قائمة العمليات أدناه:"
)

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚙️ لوحة القيادة الإدارية VIP", callback_data="btn_admin")],
        [InlineKeyboardButton("🥇 استخراج التحليل الملكي المتقدم (1M%)", callback_data="btn_signal")],
        [
            InlineKeyboardButton("🌐 الفريم: [M5]", callback_data="btn_timeframe"),
            InlineKeyboardButton("📉 العالمي + الأخبار", callback_data="btn_news")
        ],
        [InlineKeyboardButton("⚖️ الوت: [0.01]", callback_data="btn_lot")],
        [InlineKeyboardButton("💎 باقات VIP الفاخرة", callback_data="btn_prices")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك", callback_data="btn_activate")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_signal_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التحليل والسعر الفوري", callback_data="btn_signal")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="btn_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        conn = sqlite3.connect("bot_database.db", timeout=5)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, expiry, is_vip) VALUES (?, ?, ?)", 
                       (user_id, (datetime.now() - timedelta(days=1)).isoformat(), 0))
        conn.commit()
        conn.close()
    except Exception:
        pass

    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
        
    user_id = query.from_user.id
    data = query.data

    try:
        if data == "btn_signal":
            if not check_vip(user_id):
                await query.message.reply_text("❌ عذراً، هذه الميزة خاصة بمشتركي VIP فقط. تواصل مع الدعم @V8V8VN.")
                return
            
            signal = await analyze_market_signal()
            
            targets_text = f"🎯 الهدف الأول (TP1): {signal['tp1']:.2f}\n"
            if signal['tp2'] is not None:
                targets_text += f"🎯 الهدف الثاني (TP2): {signal['tp2']:.2f}\n"
            if signal['tp3'] is not None:
                targets_text += f"🎯 الهدف الثالث (TP3): {signal['tp3']:.2f}\n"

            signal_text = (
                f"🔥 التقرير التحليلي الشامل للذهب 🔥\n\n"
                f"📊 قوة الصفقة: {signal['strength']}\n"
                f"🔹 اتجاه السوق: {signal['type']}\n"
                f"🛠 الاستراتيجية والثغرة: {signal['strategy']}\n"
                f"🌍 الجلسة: {signal['session']}\n"
                f"🏛 الدولة: {signal['country']}\n"
                f"⏱ الوقت: {signal['time']}\n"
                f"🌐 الفريم: {signal['timeframe']} | ⚖️ الوت: {signal['lot']}\n"
                f"📍 سعر الدخول اللحظي: {signal['price']:.2f} $\n\n"
                f"{targets_text}"
                f"🛑 وقف الخسارة (SL): {signal['sl']:.2f}\n"
                f"🛡️ إدارة الحساب وتأمين الصفقة: {signal['secure']}"
            )
            await query.message.edit_text(signal_text, reply_markup=get_signal_keyboard())

        elif data == "btn_home":
            await query.message.edit_text(WELCOME_MESSAGE, reply_markup=get_main_keyboard())

        elif data == "btn_prices":
            await query.message.reply_text("💎 باقات VIP الفاخرة تواصل مع المعرف: @V8V8VN", reply_markup=get_main_keyboard())

        elif data == "btn_activate":
            await query.message.reply_text("🔑 لتفعيل رخصة، أرسل الأمر:\n/redeem <الكود>", reply_markup=get_main_keyboard())

        elif data == "btn_timeframe":
            await query.message.reply_text("🌐 الفريم الحالي: M5", reply_markup=get_main_keyboard())

        elif data == "btn_news":
            await query.message.reply_text("📉 أخبار السوق طبيعية ومستقرة.", reply_markup=get_main_keyboard())

        elif data == "btn_lot":
            await query.message.reply_text("⚖️ الوت الافتراضي: 0.01", reply_markup=get_main_keyboard())

        elif data == "btn_admin":
            if check_admin(user_id):
                await query.message.reply_text("🛠 لوحة الإدارة تعمل بنجاح.", reply_markup=get_main_keyboard())
            else:
                await query.message.reply_text("❌ للمشرفين فقط.")
    except Exception as e:
        logger.error(f"Error: {e}")

async def redeem_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أمر تفعيل الأكواد جاهز للاستخدام.")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("redeem", redeem_code_command))

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
