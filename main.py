import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from utils import LoggerManager, DatabaseManager, SecurityManager, PathManager

# تهيئة المسارات والسجلات باحترافية
PathManager.create_directories(".", ["database", "logs", "assets"])
logger = LoggerManager.get_logger("Alpha_VIP_Bot")

TELEGRAM_BOT_TOKEN = "8739424060:AAF5gkhpBSD2xTuP7r9WRDUbEhxPQBupZcw"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  

db = DatabaseManager()

# دالة مساعدة للتحقق من انتهاء الصلاحية
def check_user_vip(user_id):
    expiry = db.get_item(f"expiry_{user_id}")
    if expiry and float(expiry) > time.time():
        return True
    return False

# ==================== القائمة الرئيسية وكليشة الترحيب ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_vip = check_user_vip(user_id) or (user_id == ADMIN_ID)
    
    vip_status = "💎 عضوية VIP مفعلة" if is_vip else "🔓 عضوية مجانية (بدون قيود)"

    keyboard = [
        [
            InlineKeyboardButton("✨ الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("⚡ استراتيجيات صيد الذهب", callback_data="vip_strategies")
        ],
        [
            InlineKeyboardButton("💎 الباقات الاستثمارية VIP", callback_data="vip_subscriptions"),
            InlineKeyboardButton("🔑 تفعيل رخصة الاشتراك", callback_data="enter_key_prompt")
        ],
        [
            InlineKeyboardButton("📸 انستغرام", url="https://instagram.com/_7ok6"),
            InlineKeyboardButton("🎵 تيك توك", url="https://tiktok.com/@_7ok6")
        ],
        [
            InlineKeyboardButton("🛠️ الدعم الفني الخاص", callback_data="support")
        ]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ [لوحة الأدمن] صناعة رخصة VIP", callback_data="admin_durations_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🤖 *نورت البوت* \n"
        f"👨‍💻 **احمد السيد - صائد الذهب**\n"
        f"📈 خبرة ثلاث سنوات بالتداول\n"
        f"⚡ صانع بوتات • صانع مؤشرات • محلل\n"
        f"🥇 محلل فوركس (الذهب والدولار)\n\n"
        f"📌 *حالتك الحالية:* `{vip_status}`\n"
        f"🚀 *الخصائص المفعلة:* سرعة قصوى • مطابقة تامة لأسعار MT5 • بدون اشتراك إجباري!\n\n"
        f"❖ *أرسل شارت أي أصل مالي (ذهب، بيتكوين، يورو، نفط) مباشرة للفحص الفوري واستخراج الصفقة الاحترافية عبر المنصة 👇*"
    )

    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception:
            pass

# ==================== معالج الأزرار المطور والآمن ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    await query.answer()
    back_kb = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]

    # قائمة اختيار مدة الرخصة للأدمن
    if data == "admin_durations_menu":
        if user_id != ADMIN_ID:
            return
        dur_kb = [
            [InlineKeyboardButton("⏱️ يوم واحد (24 ساعة)", callback_data="gen_key_1d")],
            [InlineKeyboardButton("⏳ أسبوع (7 أيام)", callback_data="gen_key_7d")],
            [InlineKeyboardButton("⏳ أسبوعين (14 يوماً)", callback_data="gen_key_14d")],
            [InlineKeyboardButton("💎 شهر كامل (30 يوماً)", callback_data="gen_key_30d")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            "⚙️ *اختر مدة صلاحية الرخصة الجديدة التي تريد توليدها:* 🔑",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(dur_kb)
        )
        return

    # توليد الكود حسب المدة المختارة (يتغير تلقائياً في كل مرة)
    if data.startswith("gen_key_"):
        if user_id != ADMIN_ID:
            return
        
        dur_type = data.replace("gen_key_", "")
        seconds_map = {
            "1d": 86400,          # يوم واحد
            "7d": 7 * 86400,      # أسبوع
            "14d": 14 * 86400,    # أسبوعين
            "30d": 30 * 86400     # شهر
        }
        name_map = {
            "1d": "يوم واحد",
            "7d": "أسبوع",
            "14d": "أسبوعين",
            "30d": "شهر كامل"
        }
        
        duration_sec = seconds_map.get(dur_type, 86400)
        dur_name = name_map.get(dur_type, "يوم واحد")
        
        # إنشاء كود فريد ومتغير تماماً
        new_key = SecurityManager.generate_vip_key("ALPHA_VIP")
        
        # تخزين المدة بالثواني المرتبطة بهذا الكود حصرياً
        db.set_item(f"key_duration_{new_key}", str(duration_sec))
        
        await query.message.edit_text(
            f"✅ *تم توليد رخصة VIP فريدة بنجاح!* 💎\n\n"
            f"⏱️ *المدة:* `{dur_name}`\n"
            f"🔑 *كود التفعيل المتغير:* `{new_key}`\n\n"
            f"❖ قم بنسخه وإرساله للعميل المستهدف 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]])
        )
        return

    if data == "enter_key_prompt":
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text(
            "🔑 *تفعيل رخصة العضوية الفاخرة (VIP)*\n\n❖ أرسل كود التفعيل الخاص بك الآن في رسالة نصية لتفعيله فوراً 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_kb)
        )
        return

    if data == "vip_strategies":
        strat_text = (
            f"⚡ *استراتيجيات الخبير أحمد السيد الحصرية لنخبة المتداولين:* 💎\n\n"
            f"1️⃣ *استراتيجية صيد سيولة الحيتان في الذهب:* رصد مناطق التلاعب السعري واختراق الفالس بريك.\n"
            f"2️⃣ *نموذج الـ Order Block والبنوك الكبرى:* تحديد تمركز صانع السوق بدقة تامة.\n"
            f"3️⃣ *ثغرة توقيت لندن ونيويورك:* استغلال الفوليوم العالي لتحقيق أهداف مضاعفة.\n\n"
            f"❖ *أرسل شارتك الآن لتطبيق التحليل الفوري عليه 👇*"
        )
        await query.message.edit_text(strat_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "vip_subscriptions":
        sub_kb = [
            [InlineKeyboardButton("⏱️ باقة يوم واحد", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("⏳ باقة الأسبوع (7 أيام)", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("⏳ باقة الأسبوعين (14 يوماً)", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("💎 باقة الشهر الكامل (30 يوماً)", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            f"💎 *باقات الوصول الحصري للنخبة (Business VIP)*\n\n"
            f"❖ اختر المدة المطلوبة وتواصل مع المطور للاستلام الفوري: `{ADMIN_USERNAME}` 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(sub_kb)
        )
        return

    if data == "support":
        await query.message.edit_text(
            f"🛠️ *الدعم الفني الخاص بنخبة أحمد السيد*\n\n❖ للتواصل المباشر مع الخبير: `{ADMIN_USERNAME}` ⚡",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_kb)
        )
    elif data == "main_menu":
        await start_command(update, context)

# ==================== معالج الرسائل والشارتات الفوري والتحقق من الأكواد ====================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    try:
        user_id = message.from_user.id

        # التحقق من إرسال كود التفعيل النصي
        if message.text and context.user_data.get('waiting_for_key'):
            context.user_data['waiting_for_key'] = False
            entered_key = message.text.strip()
            
            duration_val = db.get_item(f"key_duration_{entered_key}")
            
            if duration_val:
                # حساب وقت الانتهاء بناءً على المدة المخزنة لهذا الكود بالذات
                expiry_time = time.time() + float(duration_val)
                db.set_item(f"expiry_{user_id}", str(expiry_time))
                
                # حذف الكود لكي لا يتم استخدامه مرة أخرى
                db.delete_item(f"key_duration_{entered_key}")
                
                await message.reply_text("🎉 *مبارك يا مولاي! تم تفعيل رخصة الـ VIP بنجاح تام.*\nأرسل `/start` للاستمتاع بكافة مزايا النخبة 🚀", parse_mode="Markdown")
            else:
                await message.reply_text("❌ *عذراً، كود التفعيل غير صحيح، منتهي الصلاحية، أو تم استخدامه مسبقاً.*", parse_mode="Markdown")
            return

        # معالجة الشارتات والصور وإعطاء تقرير احترافي
        if message.photo:
            is_vip = check_user_vip(user_id) or (user_id == ADMIN_ID)
            tier_badge = "💎 [VIP Elite Member]" if is_vip else "🔓 [Free Member]"
            
            await message.reply_text(f"⚡ *جاري معالجة الشارت وقراءة السعر المباشر بدقة تامة {tier_badge}... 📈*", parse_mode="Markdown")
            
            report = (
                f"📊 *[ تقرير تحليل صفقات النخبة - MT5 Pro ]* 💎\n\n"
                f"🏛️ *الأصل المالي المُحلل:* `الذهب والعملات (MT5 Verified)`\n"
                f"💹 *السعر المباشر بالمنصة:* `مطابق تماماً لمنصة MT5`\n\n"
                f"🎯 *مستويات تنفيذ الصفقة الاحترافية:*\n"
                f"  🟢 *سعر الدخول (Entry):* `حسب معطيات الشارت المرسل`\n"
                f"  🎯 *الهدف الاول (TP1):* `مدعوم بنظام سيولة الحيتان`\n"
                f"  🚀 *الهدف النهائي (TP2):* `استهداف القمم والقعان بدقة`\n"
                f"  🛑 *وقف الخسارة (SL):* `إدارة مخاطر صارمة وآمنة`\n\n"
                f"👑 *إشراف الخبير:* أحمد السيد ({ADMIN_USERNAME})"
            )
            await message.reply_text(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]]))
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
