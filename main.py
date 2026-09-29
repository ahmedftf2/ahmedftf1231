import logging
import sqlite3
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from utils import (
    init_db, analyze_market_signal, redeem_vip_code, 
    create_vip_code, get_all_users_stats, ban_user_in_db, is_user_banned
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"
ADMIN_IDS = [5796443586]
REQUIRED_CHANNEL = "@FOR2AH"

init_db()

def check_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def check_forced_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if user_id in ADMIN_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass
    return False

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

def get_main_keyboard(is_admin: bool = False):
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
    if is_admin:
        keyboard.insert(1, [InlineKeyboardButton("📢 نشر الصفقة مباشرة للقناة", callback_data="btn_publish_channel")])
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔑 توليد كود VIP جاهز تلقائياً (30 يوم)", callback_data="admin_gen_code")],
        [InlineKeyboardButton("👥 عرض قائمة المشتركين والأيدي (ID)", callback_data="admin_list_users")],
        [InlineKeyboardButton("🚫 حظر مستخدم (عبر الأيدي)", callback_data="admin_ban_menu")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="btn_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_signal_keyboard(is_admin: bool = False):
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التحليل والسعر الفوري", callback_data="btn_signal")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("📢 نشر هذه الصفقة للقناة الآن", callback_data="btn_publish_channel")])
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="btn_home")])
    return InlineKeyboardMarkup(keyboard)

def get_subscription_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة الرسمية", url="https://t.me/FOR2AH")],
        [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="btn_check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_user_banned(user_id):
        await update.message.reply_text("❌ عذراً، لقد تم حظرك من استخدام هذا البوت.")
        return

    if not await check_forced_subscription(user_id, context):
        await update.message.reply_text(
            f"❌ عذراً يا غالي، يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه:\n{REQUIRED_CHANNEL}\n\nبعد الاشتراك، اضغط على زر التحقق أدناه 👇",
            reply_markup=get_subscription_keyboard()
        )
        return

    try:
        conn = sqlite3.connect("bot_database.db", timeout=5)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, expiry, is_vip) VALUES (?, ?, ?, ?, ?)", 
            (user_id, update.effective_user.username or "N/A", update.effective_user.full_name or "N/A", (datetime.now() - timedelta(days=1)).isoformat(), 0)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_keyboard(check_admin(user_id))
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
        
    user_id = query.from_user.id
    data = query.data
    is_adm = check_admin(user_id)

    if is_user_banned(user_id):
        await query.message.edit_text("❌ حسابك محظور من استخدام البوت.")
        return

    if data == "btn_check_sub":
        if await check_forced_subscription(user_id, context):
            await query.message.edit_text(WELCOME_MESSAGE, reply_markup=get_main_keyboard(is_adm))
        else:
            await query.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)
        return

    if not await check_forced_subscription(user_id, context):
        try:
            await query.message.edit_text(
                f"❌ عذراً، يجب عليك الاشتراك في القناة أولاً: {REQUIRED_CHANNEL}",
                reply_markup=get_subscription_keyboard()
            )
        except Exception:
            await query.message.reply_text(
                f"❌ عذراً، يجب عليك الاشتراك في القناة أولاً: {REQUIRED_CHANNEL}",
                reply_markup=get_subscription_keyboard()
            )
        return

    try:
        if data == "btn_signal":
            if not check_vip(user_id):
                await query.message.edit_text("❌ عذراً، هذه الميزة خاصة بمشتركي VIP. تواصل مع الدعم @V8V8VN لتفعيل اشتراكك.", reply_markup=get_main_keyboard(is_adm))
                return
            
            signal = await analyze_market_signal()
            context.user_data['last_signal'] = signal
            
            targets_text = f"🎯 الهدف الأول (TP1): {signal['tp1']:.2f}\n"
            if signal['tp2'] is not None:
                targets_text += f"🎯 الهدف الثاني (TP2): {signal['tp2']:.2f}\n"
            if signal['tp3'] is not None:
                targets_text += f"🎯 الهدف الثالث (TP3): {signal['tp3']:.2f}\n"

            signal_text = (
                f"🔥 التقرير التحليلي الشامل للذهب 🔥\n\n"
                f"📊 قوة الصفقة: {signal['strength']}\n"
                f"🎯 **نسبة دقة وتاكيد الصفقة: {signal['accuracy']}%** 📈\n"
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
            await query.message.edit_text(signal_text, reply_markup=get_signal_keyboard(is_adm))

        elif data == "btn_publish_channel":
            if not is_adm:
                await query.answer("❌ هذه الميزة مخصصة للآدمن فقط!", show_alert=True)
                return
            
            signal = context.user_data.get('last_signal')
            if not signal:
                signal = await analyze_market_signal()
            
            targets_text = f"🎯 الهدف الأول (TP1): {signal['tp1']:.2f}\n"
            if signal['tp2'] is not None:
                targets_text += f"🎯 الهدف الثاني (TP2): {signal['tp2']:.2f}\n"
            if signal['tp3'] is not None:
                targets_text += f"🎯 الهدف الثالث (TP3): {signal['tp3']:.2f}\n"

            channel_text = (
                f"🦅 **توصية رسمية من قناة أحمد السيد للذهب** 🦅\n\n"
                f"📊 قوة الصفقة: {signal['strength']}\n"
                f"🎯 **نسبة دقة وتاكيد الصفقة: {signal['accuracy']}%** 📈\n"
                f"🔹 اتجاه السوق: {signal['type']}\n"
                f"🛠 الاستراتيجية والثغرة: {signal['strategy']}\n"
                f"📍 سعر الدخول اللحظي: {signal['price']:.2f} $\n\n"
                f"{targets_text}"
                f"🛑 وقف الخسارة (SL): {signal['sl']:.2f}\n"
                f"🛡️ {signal['secure']}\n\n"
                f"💎 للتفعيل والانضمام للبوت الاحترافي: @V8V8VN"
            )
            
            await context.bot.send_message(chat_id=REQUIRED_CHANNEL, text=channel_text)
            await query.answer("✅ تم نشر الصفقة في القناة بنجاح تام!", show_alert=True)

        elif data == "btn_home":
            await query.message.edit_text(WELCOME_MESSAGE, reply_markup=get_main_keyboard(is_adm))

        elif data == "btn_prices":
            await query.message.edit_text("💎 باقات VIP الفاخرة لتفعيل الأكواد، تواصل مع المعرف: @V8V8VN", reply_markup=get_main_keyboard(is_adm))

        elif data == "btn_activate":
            await query.message.edit_text("🔑 لتفعيل رخصة الاشتراك، أرسل الأمر:\n`/redeem <كود_التفعيل>` في الشات العام.", reply_markup=get_main_keyboard(is_adm))

        elif data == "btn_timeframe":
            await query.message.edit_text("🌐 الفريم الحالي: M5", reply_markup=get_main_keyboard(is_adm))

        elif data == "btn_news":
            await query.message.edit_text("📉 أخبار السوق طبيعية ومستقرة.", reply_markup=get_main_keyboard(is_adm))

        elif data == "btn_lot":
            await query.message.edit_text("⚖️ الوت الافتراضي: 0.01", reply_markup=get_main_keyboard(is_adm))

        elif data == "btn_admin":
            if is_adm:
                await query.message.edit_text(
                    "🛠 **لوحة التحكم الإدارية الاحترافية**\nاختر العملية المطلوبة أدناه:",
                    reply_markup=get_admin_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await query.answer("❌ هذه اللوحة مخصصة للمشرفين فقط!", show_alert=True)

        elif data == "admin_gen_code":
            if not is_adm:
                return
            # توليد كود عشوائي جاهز
            random_code = "VIP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            create_vip_code(random_code, 30)
            await query.message.edit_text(
                f"✅ **تم إنشاء كود VIP جديد بنجاح!**\n\n"
                f"🔑 الكود الجاهز: `{random_code}`\n"
                f"⏳ المدة: 30 يوماً\n\n"
                f"انسخ هذا الكود وأعطه للمشترك لتفعيله.",
                reply_markup=get_admin_keyboard(),
                parse_mode="Markdown"
            )

        elif data == "admin_list_users":
            if not is_adm:
                return
            users = get_all_users_stats()
            if not users:
                text = "📁 لا يوجد مشتركين مسجلين في قاعدة البيانات حتى الآن."
            else:
                text = "👥 **قائمة المشتركين في البوت:**\n\n"
                for u in users:
                    u_id, username, full_name, expiry = u
                    text += f"👤 الاسم: {full_name}\n🆔 الايدي: `{u_id}`\n🔗 المعرف: @{username}\n⏳ انتهاء الـ VIP: {expiry[:10] if expiry else 'غير مشترك'}\n-------------------\n"
            await query.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

        elif data == "admin_ban_menu":
            if not is_adm:
                return
            await query.message.edit_text(
                "🚫 **حظر مستخدم:**\n\nلإحالة أي مستخدم إلى القائمة السوداء، أرسل الأمر بالشكل التالي في الشات:\n`/ban <أيدي_المستخدم>`\n\nولإلغاء الحظر أرسل:\n`/unban <أيدي_المستخدم>`",
                reply_markup=get_admin_keyboard(),
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Error: {e}")

async def redeem_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        return
    if not context.args:
        await update.message.reply_text("❌ يرجى كتابة الكود بعد الأمر.\nمثال: `/redeem VIP-123`")
        return
    
    code = context.args[0]
    success, message = redeem_vip_code(user_id, code)
    await update.message.reply_text(message)

async def add_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_admin(user_id):
        await update.message.reply_text("❌ عذراً، هذا الأمر مخصص للمشرفين فقط.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ الاستخدام الخاطئ.\nالطريقة الصحيحة:\n`/addcode <الكود> <عدد_الأيام>`", parse_mode="Markdown")
        return
    
    code = context.args[0]
    try:
        days = int(context.args[1])
        create_vip_code(code, days)
        await update.message.reply_text(f"✅ **تم إنشاء كود الـ VIP بنجاح!**\n\n🔑 الكود: `{code}`\n⏳ المدة: {days} يوم", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {e}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_admin(user_id):
        return
    if not context.args:
        await update.message.reply_text("❌ اكتب الأيدي بعد الأمر.\nمثال: `/ban 123456789`")
        return
    try:
        target_id = int(context.args[0])
        ban_user_in_db(target_id, 1)
        await update.message.reply_text(f"✅ تم حظر المستخدم ذو الأيدي `{target_id}` بنجاح.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {e}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_admin(user_id):
        return
    if not context.args:
        await update.message.reply_text("❌ اكتب الأيدي بعد الأمر.\nمثال: `/unban 123456789`")
        return
    try:
        target_id = int(context.args[0])
        ban_user_in_db(target_id, 0)
        await update.message.reply_text(f"✅ تم رفع الحظر عن المستخدم `{target_id}` بنجاح.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {e}")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("redeem", redeem_code_command))
    application.add_handler(CommandHandler("addcode", add_code_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
