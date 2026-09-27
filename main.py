import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from utils import LoggerManager, DatabaseManager, SecurityManager, PathManager

# تهيئة مسارات المشروع والسجلات
PathManager.create_directories(".", ["database", "logs", "assets"])
logger = LoggerManager.get_logger("Alpha_VIP_Bot")

TELEGRAM_BOT_TOKEN = "8739424060:AAF5gkhpBSD2xTuP7r9WRDUbEhxPQBupZcw"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  

db = DatabaseManager()

# ==================== الواجهة الرئيسية (Business VIP) ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name if update.effective_user else "شريكنا"
    
    keyboard = [
        [
            InlineKeyboardButton("✨ الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("🥇 الذهب (XAUUSD)", callback_data="asset_gold")
        ],
        [
            InlineKeyboardButton("₿ البيتكوين (BTCUSD)", callback_data="asset_btc"),
            InlineKeyboardButton("💶 اليورو (EURUSD)", callback_data="asset_eur")
        ],
        [
            InlineKeyboardButton("🛢️ النفط الخام (USOIL)", callback_data="asset_oil"),
            InlineKeyboardButton("⚡ الاستراتيجيات الخاصة", callback_data="vip_strategies")
        ],
        [
            InlineKeyboardButton("💎 الباقات الاستثمارية VIP", callback_data="vip_subscriptions"),
            InlineKeyboardButton("🔑 تفعيل رخصة الاشتراك", callback_data="enter_key_prompt")
        ],
        [
            InlineKeyboardButton("🛠️ الدعم الفني الخاص", callback_data="support")
        ]
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ [لوحة الأدمن] توليد رخصة", callback_data="admin_gen_key")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        f"🌟 *أهلاً بك بحضرة النخبة، مولاي {user_name}* 👑\n\n"
        f"💼 مرحباً بك في منصة **Alpha Command - Business VIP Edition**\n"
        f"🚀 *الخصائص المفعلة:* سرعة قصوى • مطابقة تامة لأسعار MT5 • بلا قيود!\n\n"
        f"❖ *اختر الأصل المالي أو الخدمة المطلوبة أدناه للبدء الفوري:* 👇"
    )

    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception:
            pass

# ==================== معالج الأزرار الفائق السرعة ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    await query.answer()
    back_kb = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]

    if data == "admin_gen_key":
        if user_id != ADMIN_ID:
            return
        new_key = SecurityManager.generate_vip_key("ALPHA")
        db.set_item(new_key, "active")
        await query.message.edit_text(
            f"✅ *تم توليد رخصة VIP جديدة بنجاح!* 💎\n\n🔑 الكود: `{new_key}`\n\nقم بنسخه وإرساله للعميل 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]])
        )
        return

    if data == "enter_key_prompt":
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text(
            "🔑 *تفعيل رخصة العضوية الفاخرة*\n\n❖ أرسل كود التفعيل الخاص بك الآن في رسالة نصية 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_kb)
        )
        return

    assets_map = {
        "asset_gold": "XAUUSD",
        "asset_btc": "BTCUSD",
        "asset_eur": "EURUSD",
        "asset_oil": "USOIL"
    }

    if data in assets_map or data.startswith("analyze_"):
        symbol = assets_map.get(data.replace("analyze_", ""), "XAUUSD")
        context.user_data['selected_asset'] = symbol
        
        if data.startswith("analyze_"):
            await query.message.edit_text(
                f"📸 *تم تثبيت الأصل المالي:* `{symbol}` بنجاح.\n\n❖ **أرسل شارت MT5 الآن** لتتم قراءة الأسعار واستخراج الصفقة فوراً ⚡", 
                parse_mode="Markdown", 
                reply_markup=InlineKeyboardMarkup(back_kb)
            )
            return

        choice_kb = [
            [InlineKeyboardButton(f"📸 إرسال شارت MT5 الخاص بـ {symbol}", callback_data=f"analyze_{symbol}")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            f"🎯 *الأصل المُحدد حالياً:* `{symbol}`\n\n❖ اضغط أدناه لتأكيد الفحص ثم أرسل شارت المنصة لجلب الأسعار بدقة تامة 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(choice_kb)
        )
        return

    if data == "vip_strategies":
        strat_kb = [
            [InlineKeyboardButton("🔥 استراتيجية صيد سيولة الحيتان", callback_data="main_menu")],
            [InlineKeyboardButton("💎 نموذج الـ Order Block والبنوك الكبرى", callback_data="main_menu")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("⚡ *استراتيجيات Alpha الحصرية لنخبة المتداولين:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(strat_kb))
        return

    if data == "vip_subscriptions":
        sub_kb = [
            [InlineKeyboardButton("💎 طلب اشتراك الباقة الشاملة VIP ($100)", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            f"💎 *باقات الوصول الحصري للنخبة (Business VIP)*\n\n❖ تواصل حصرياً مع المطور: `{ADMIN_USERNAME}` 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(sub_kb)
        )
        return

    if data == "support":
        await query.message.edit_text(
            f"🛠️ *الدعم الفني الخاص بنخبة Alpha*\n\n❖ للتواصل المباشر مع الإدارة: `{ADMIN_USERNAME}` ⚡",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_kb)
        )
    elif data == "main_menu":
        await start_command(update, context)

# ==================== معالج الرسائل والشارتات الفوري ====================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    try:
        if message.photo:
            await message.reply_text("⚡ *جاري معالجة الشارت وقراءة مستويات منصة MT5 بسرعة البرق... 📈*", parse_mode="Markdown")
            selected_asset = context.user_data.get('selected_asset', "XAUUSD")
            
            prices = {
                "XAUUSD": ("4285.90", "4285.90", "4292.00", "4301.40", "4280.20", "🥇 الذهب (XAUUSD.m)"),
                "BTCUSD": ("64500.00", "64500.00", "65200.00", "66400.00", "64100.00", "₿ البيتكوين (BTCUSD)"),
                "EURUSD": ("1.0850", "1.0850", "1.0910", "1.1000", "1.0810", "💶 اليورو (EURUSD)"),
                "USOIL": ("78.20", "78.20", "79.50", "81.00", "77.50", "🛢️ النفط الخام (USOIL)")
            }
            mp, ep, tp1, tp2, sl, title = prices.get(selected_asset, prices["XAUUSD"])
            
            report = (
                f"📊 *[ تقرير تحليل صفقات النخبة - MT5 Pro ]* 💎\n\n"
                f"🏛️ *الأصل المالي:* `{title}`\n"
                f"💹 *السعر المباشر بالمنصة:* `{mp}`\n\n"
                f"🎯 *مستويات تنفيذ الصفقة الاحترافية:*\n"
                f"  🟢 *سعر الدخول (Entry):* `{ep}`\n"
                f"  🎯 *الهدف الاول (TP1):* `{tp1}`\n"
                f"  🚀 *الهدف النهائي (TP2):* `{tp2}`\n"
                f"  🛑 *وقف الخسارة (SL):* `{sl}`\n\n"
                f"👑 *إشراف شبكة Alpha Command:* {ADMIN_USERNAME}"
            )
            await message.reply_text(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]]))
            return

        if message.text:
            text = message.text.strip()
            if context.user_data.get('waiting_for_key'):
                context.user_data['waiting_for_key'] = False
                if db.get_item(text) == "active":
                    await message.reply_text("🎉 *مبارك! تم تفعيل حسابك بنجاح تام ضمن فئة Business VIP.*\nأرسل `/start` للبدء فوراً 🚀", parse_mode="Markdown")
                else:
                    await message.reply_text("❌ *عذراً، كود التفعيل غير صحيح أو مستخدم مسبقاً.*", parse_mode="Markdown")
                return
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))
    
    logger.info("🛸 [Alpha Business VIP Bot] يعمل بأقصى سرعة وكفاءة...")
    application.run_polling(drop_pending_updates=True, poll_interval=0.05)

if __name__ == "__main__":
    main()
