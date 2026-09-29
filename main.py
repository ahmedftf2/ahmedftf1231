import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
from utils import (
    init_db, redeem_vip_code, create_vip_code, 
    get_all_users_stats, ban_user_in_db, is_user_banned,
    analyze_chart_screenshot, analyze_market_signal
)

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"  # ضع توكن البوت الخاص بك هنا
ADMIN_IDS = [123456789]        # ضع الآيدي الخاص بك هنا

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def check_vip(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    try:
        import sqlite3
        conn = sqlite3.connect("bot_database.db", timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT expiry FROM users WHERE user_id = ? AND is_vip = 1", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            expiry_date = datetime.fromisoformat(row[0])
            if expiry_date > datetime.now():
                return True
    except Exception:
        pass
    return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if is_user_banned(user_id):
        await update.message.reply_text("⛔ تم حظر وصولك إلى هذه الخزنة السيبرانية.")
        return

    try:
        import sqlite3
        conn = sqlite3.connect("bot_database.db", timeout=5)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username, full_name, expiry, is_vip, is_banned)
            VALUES (?, ?, ?, NULL, 0, 0)
        """, (user_id, user.username or "", user.full_name or ""))
        conn.commit()
        conn.close()
    except Exception:
        pass

    welcome_text = (
        f"🏴‍☠️ **مرحباً بك في المحطة السرية المطلقة لعالم الذهب (XAU/USD)** 🏴‍☠️\n\n"
        f"أنت الآن تقف أمام السلاح المالي الأشرس والأكثر هيبة في أسواق المال العالمية..\n"
        f"أنا النظام الذكي المصمم خصيصاً بإشراف مباشر من الخبير الأسطوري والعقل المدبر **أحمد السيد** 👁‍🗨.\n\n"
        f"⚡ **من هو الخبير أحمد السيد وماذا نقدم لك هنا؟**\n"
        f"• **أحمد السيد:** خبير الاستراتيجيات الكمية وهندسة السيولة المؤسسية، صاحب البصمة الأدق في قراءة صانع السوق واقتناص الصفقات الخارقة دون رحمة.\n"
        f"• **ما نقدمه:** قراءة حية ومباشرة للشارت عبر الذكاء الاصطناعي، تحليل سكرين الشاشة بدقة 99.999%، كشف فخاخ السوق، وتأمين صفقات بنسب مخاطرة إلى عائد فلكية (`1:12`).\n\n"
        f"🌌 **قنوات التواصل والمعرفات الرسمية للسيادة:**\n"
        f"• المعرف الشخصي لدعم الخبير: `@V8V8VN`\n\n"
        f"اختر طريقتك ودعنا نبتلع السوق معاً.."
    )

    keyboard = [
        [InlineKeyboardButton("⚜️ الفحص السيبراني المباشر للشارت ⚜️", callback_data="btn_signal")],
        [InlineKeyboardButton("🔮 إرسال سكرين الشاشة للتحليل الأسطوري 🔮", callback_data="btn_screen_info")],
        [InlineKeyboardButton("🗝️ بوابة تفعيل شفرة النخبة VIP 🗝️", callback_data="btn_vip_info")],
        [InlineKeyboardButton("💀 قنوات الإمبراطورية والحسابات الرسمية 💀", callback_data="btn_channels")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if is_user_banned(user_id):
        return

    data = query.data

    if data == "btn_signal":
        if not check_vip(user_id):
            await query.edit_message_text(
                "🔒 **بوابة النخبة مغلقة في وجهك!**\n\n"
                "هذا التحليل الإمبراطوري مخصص لحاملي رتبة الـ VIP فقط بناءً على توجيهات الخبير **أحمد السيد**.\n"
                "للحصول على شفرة الدخول، تواصل فوراً مع المعرف المعتمد: @V8V8VN",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقصر", callback_data="back_home")]])
            )
            return

        loading_msg = await query.edit_message_text("⚡ **جاري اختراق السيرفرات وتحليل خريطة السيولة والشموع الخفية.. انتظر قليلاً..**")
        
        signal = await analyze_market_signal()
        
        targets_text = (
            f"🎯 الهدف الأول (TP1): `{signal['tp1']:.2f}`\n"
            f"🎯 الهدف الثاني (TP2): `{signal['tp2']:.2f}`\n"
            f"🎯 الهدف الثالث (TP3): `{signal['tp3']:.2f}`\n"
        )

        result_text = (
            f"👑 **تقرير الخبير أحمد السيد - الصفقة الإمبراطورية المؤكدة** 👑\n\n"
            f"👁‍🗨 حالة السيولة: `{signal['strength']}`\n"
            f"🎯 **معامل الدقة المطلقة: {signal['accuracy']}%** 📈\n"
            f"⚖️ نسبة المخاطرة للعائد: `{signal['risk_reward']}`\n"
            f"🔹 اتجاه العملية: `{signal['type']}`\n"
            f"🛠 الاستراتيجيات المشفرة: `{signal['strategy']}`\n"
            f"🌍 نطاق الجلسة: `{signal['session']}`\n"
            f"⏱ التوقيت القياسي: `{signal['time']}`\n"
            f"🌐 الفريم الزمني: `{signal['timeframe']}` | ⚖️ الوت: `{signal['lot']}`\n"
            f"📍 سعر الدخول الحي: `{signal['price']:.2f} $`\n\n"
            f"{targets_text}\n"
            f"🛑 خط الأمان ووقف الخسارة (SL): `{signal['sl']:.2f}`\n"
            f"🛡️ خطة الحماية والدفاع: `{signal['secure']}`\n\n"
            f"⚡ *نفذ الصفقة بثقة الإمبراطور ولا تلتفت للوراء.*"
        )
        
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقصر", callback_data="back_home")]])
        await loading_msg.edit_text(result_text, reply_markup=back_kb)

    elif data == "btn_screen_info":
        await query.edit_message_text(
            "🔮 **تفعيل ميزة تحليل شكرين الشاشة الإمبراطوري** 🔮\n\n"
            "لكي يقرأ الذكاء الاصطناعي الشارت الخاص بك ككتاب مفتوح تحت إشراف الخبير **أحمد السيد**:\n"
            "• قم ببساطة **بإرسال صورة (سكرين شاشة للشارت)** مباشرة هنا في المحادثة.\n"
            "• سيقوم النظام السيبراني بفك طلاسم الشمعات وإرجاع الصفقة الجاهزة والمحفوظة بأعلى درجات الدقة فوراً.\n\n"
            "*(ملاحظة: الميزة حصصرية لرتبة الـ VIP والمشتركين النشطين)*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقصر", callback_data="back_home")]])
        )

    elif data == "btn_vip_info":
        await query.edit_message_text(
            "🗝️ **بوابة شفرات النخبة والسيادة VIP** 🗝️\n\n"
            "للحصول على المفتاح السري ودخول الخزائن الحصرية للمحلل **أحمد السيد**:\n"
            "1. تواصل مباشرة مع الدعم الإمبراطوري: `@V8V8VN`\n"
            "2. اطلب شفرة التفعيل الخاصة بك.\n"
            "3. أرسل الشفرة هنا عبر الأمر التالي:\n"
            "`/redeem [الشفرة]`\n\n"
            "لتنفتح لك أبواب الذهب على مصراعيها.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقصر", callback_data="back_home")]])
        )

    elif data == "btn_channels":
        await query.edit_message_text(
            "💀 **القنوات والحسابات الرسمية للإمبراطورية** 💀\n\n"
            "• المعرف الشخصي للخبير **أحمد السيد**: `@V8V8VN`\n\n"
            "كن دائمًا في القمة ولا ترضى بغير الصدارة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقصر", callback_data="back_home")]])
        )

    elif data == "back_home":
        welcome_text = (
            f"🏴‍☠️ **مرحباً بك مجدداً في المحطة السرية الإمبراطورية** 🏴‍☠️\n\n"
            f"بإشراف مباشر من الخبير الأسطوري **أحمد السيد** 👁‍🗨.\n"
            f"اختر وجهتك التالية لتستمر في حصد أرباح الأسواق.."
        )
        keyboard = [
            [InlineKeyboardButton("⚜️ الفحص السيبراني المباشر للشارت ⚜️", callback_data="btn_signal")],
            [InlineKeyboardButton("🔮 إرسال سكرين الشاشة للتحليل الأسطوري 🔮", callback_data="btn_screen_info")],
            [InlineKeyboardButton("🗝️ بوابة تفعيل شفرة النخبة VIP 🗝️", callback_data="btn_vip_info")],
            [InlineKeyboardButton("💀 قنوات الإمبراطورية والحسابات الرسمية 💀", callback_data="btn_channels")]
        ]
        await query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_chart_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        return
        
    if not check_vip(user_id):
        await update.message.reply_text("❌ عذراً يا صديقي، عيون الحراسة تمنعك من تحليل الشارتات.. هذه الخاصية لحاملي رتبة الـ VIP فقط. تواصل مع الخبير أحمد السيد: @V8V8VN")
        return

    processing_msg = await update.message.reply_text("👁‍🗨 **جاري التقاط الشارت وفك طلاسمه عبر خوارزميات الخبير أحمد السيد.. لحظات ويسلمك الصفقة الملكية..** ⚡")

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    signal = await analyze_chart_screenshot(photo_bytes)
    
    targets_text = (
        f"🎯 الهدف الأول (TP1): `{signal['tp1']:.2f}`\n"
        f"🎯 الهدف الثاني (TP2): `{signal['tp2']:.2f}`\n"
        f"🎯 الهدف الثالث (TP3): `{signal['tp3']:.2f}`\n"
    )

    result_text = (
        f"🦅 **تحليل سكرين الشاشة الإمبراطوري - الخبير أحمد السيد** 🦅\n\n"
        f"👁‍🗨 حالة الرصد: `{signal['strength']}`\n"
        f"🎯 **الدقة المؤكدة: {signal['accuracy']}%** 📈\n"
        f"⚖️ نسبة المخاطرة للعائد: `{signal['risk_reward']}`\n"
        f"🔹 الاتجاه المعتمد: `{signal['type']}`\n"
        f"🛠 الاستراتيجيات المقكدسة: `{signal['strategy']}`\n"
        f"🌍 الجلسة: `{signal['session']}`\n"
        f"⏱ وقت الفحص: `{signal['time']}`\n"
        f"🌐 الفريم: `{signal['timeframe']}` | ⚖️ الوت: `{signal['lot']}`\n"
        f"📍 سعر الدخول: `{signal['price']:.2f} $`\n\n"
        f"{targets_text}\n"
        f"🛑 وقف الخسارة (SL): `{signal['sl']:.2f}`\n"
        f"🛡️ نظام الأمان: `{signal['secure']}`\n\n"
        f"💎 *جاهزة للتنفيذ الفوري في منصتك برعاية أحمد السيد.*"
    )

    await processing_msg.edit_text(result_text)

async def redeem_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        return
        
    if not context.args:
        await update.message.reply_text("⚠️ صيغة خاطئة يا صاحب السيادة. استخدم الأمر هكذا:\n`/redeem [الشفرة]`")
        return
        
    code = context.args[0]
    success, msg = redeem_vip_code(user_id, code)
    await update.message.reply_text(msg)

async def add_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ استخدام الأدمن: `/addcode [الشفرة] [الأيام]`")
        return
        
    try:
        code = context.args[0]
        days = float(context.args[1])
        create_vip_code(code, days)
        await update.message.reply_text(f"✅ تم زرع الشفرة الإمبراطورية `{code}` لمدة `{days}` أيام بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    if not context.args:
        return
    try:
        target_id = int(context.args[0])
        ban_user_in_db(target_id, 1)
        await update.message.reply_text(f"⛔ تم حظر المستخدم `{target_id}` وعزله عن الإمبراطورية.")
    except Exception:
        pass

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    if not context.args:
        return
    try:
        target_id = int(context.args[0])
        ban_user_in_db(target_id, 0)
        await update.message.reply_text(f"🔓 تم رفع الحظر عن المستخدم `{target_id}` وإعادته للقصر.")
    except Exception:
        pass

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("redeem", redeem_code_command))
    application.add_handler(CommandHandler("addcode", add_code_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_chart_photo))

    print("👑 [SECURITY LEVEL: MAXIMUM] البوت الإمبراطورية يعمل الآن بحماية مطلقة وتحت إدارة الخبير أحمد السيد...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
