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
    is_admin = (user_id == ADMIN_ID)
    is_vip = check_user_vip(user_id) or is_admin
    
    vip_status = "💎 عضوية VIP مفعلة" if is_vip else "🔓 عضوية مجانية (بدون قيود)"

    keyboard = [
        [
            InlineKeyboardButton("✨ الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("🥇 الذهب (XAUUSD)", callback_data="signal_gold"),
            InlineKeyboardButton("💶 العملات (Forex)", callback_data="signal_forex")
        ],
        [
            InlineKeyboardButton("🪙 البيتكوين (BTC)", callback_data="signal_crypto"),
            InlineKeyboardButton("🛢️ النفط الخام (Oil)", callback_data="signal_oil")
        ],
        [
            InlineKeyboardButton("⚡ الاستراتيجيات الثلاثة", callback_data="vip_strategies"),
            InlineKeyboardButton("📍 الدولة والجلسات", callback_data="country_info")
        ],
        [
            InlineKeyboardButton("💎 الباقات الاستثمارية VIP", callback_data="vip_subscriptions"),
            InlineKeyboardButton("🔑 تفعيل رخصة الاشتراك", callback_data="enter_key_prompt")
        ],
        [
            InlineKeyboardButton("📸 انستغرام", url="https://instagram.com/_7ok6"),
            InlineKeyboardButton("🎵 تيك توك", url="https://tiktok.com/@7ok6_")
        ],
        [
            InlineKeyboardButton("🛠️ الدعم الفني للاشتراك", callback_data="support")
        ]
    ]

    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ [لوحة الأدمن] صناعة رخصة VIP المتغيرة", callback_data="admin_durations_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🤖 مرحباً بك في بوت وتوصيات أحمد السيد للذهب 🥇\n\n"
        f"👨‍💻 **المطور والخبير:** احمد السيد - صائد الذهب\n"
        f"📈 خبرة ثلاث سنوات بالتداول • محلل فوركس (الذهب والدولار)\n\n"
        f"📌 *حالتك الحالية:* `{vip_status}`\n"
        f"🚀 *الخصائص:* صفقات فورية بدون سكرين عبر الأزرار + تحليل شارتات MT5 المباشرة!\n\n"
        f"❖ *اختر أصل التداول أدناه للحصول على صفقة مباشرة، أو أرسل شارت الشاشة للفحص 👇*"
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
    is_admin = (user_id == ADMIN_ID)

    await query.answer()
    back_kb = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]

    # 1. لوحة الأدمن لتوليد الأكواد
    if data == "admin_durations_menu":
        if not is_admin:
            return
        dur_kb = [
            [InlineKeyboardButton("⏱️ يوم واحد (24 ساعة)", callback_data="gen_key_1d")],
            [InlineKeyboardButton("⏳ أسبوع (7 أيام)", callback_data="gen_key_7d")],
            [InlineKeyboardButton("⏳ أسبوعين (14 يوماً)", callback_data="gen_key_14d")],
            [InlineKeyboardButton("💎 شهر كامل (30 يوماً)", callback_data="gen_key_30d")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            "⚙️ *لوحة الأدمن: اختر مدة صلاحية الرخصة الجديدة لتوليد كود فريد ومختلف:* 🔑",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(dur_kb)
        )
        return

    if data.startswith("gen_key_"):
        if not is_admin:
            return
        
        dur_type = data.replace("gen_key_", "")
        seconds_map = {"1d": 86400, "7d": 7 * 86400, "14d": 14 * 86400, "30d": 30 * 86400}
        name_map = {"1d": "يوم واحد", "7d": "أسبوع", "14d": "أسبوعين", "30d": "شهر كامل"}
        
        duration_sec = seconds_map.get(dur_type, 86400)
        dur_name = name_map.get(dur_type, "يوم واحد")
        
        new_key = SecurityManager.generate_vip_key("ALPHA_VIP")
        db.set_item(f"key_duration_{new_key}", str(duration_sec))
        
        await query.message.edit_text(
            f"✅ *تم توليد رخصة VIP فريدة ومخصصة بنجاح!* 💎\n\n"
            f"⏱️ *المدة المحددة:* `{dur_name}`\n"
            f"🔑 *كود التفعيل (متغير وخاص):* `{new_key}`\n\n"
            f"❖ قم بنسخه وإرساله للشخص المعني للاستلام 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]])
        )
        return

    # 2. الصفقات الفورية بدون سكرين شاشة (مع الجلسة، الدولة، الفريم، الأهداف، وتأمين الصفقة)
    if data == "signal_gold":
        gold_signal = (
            f"🥇 *[ صفقة فورية مباشرة: الذهب XAUUSD ]* 💎\n\n"
            f"🏛️ *منصة التنفيذ:* `MT5 Pro (مطابق 100%)`\n"
            f"🌍 *الجلسة والدولة:* `جلسة لندن / نيويورك (المملكة المتحدة والولايات المتحدة)`\n"
            f"⏱️ *الفريم الزمني الناجح:* `15 دقيقة / 30 دقيقة (متوسط المدى)`\n\n"
            f"🎯 *تفاصيل الصفقة الاحترافية:*\n"
            f"  🟢 *نوع الإشارة:* `شراء (BUY) من مناطق سيولة الحيتان`\n"
            f"  📍 *سعر الدخول (Entry):* `السعر الحالي المباشر أو إعادة اختبار الدعم`\n"
            f"  🎯 *الهدف الأول (TP1):* `حصد النصف عند مقاومة قريبة`\n"
            f"  🎯 *الهدف الثاني (TP2):* `امتداد السيولة المنتصف`\n"
            f"  🚀 *الهدف الثالث النهائي (TP3):* `استهداف قمة الهيكل الكبرى`\n"
            f"  🛑 *وقف الخسارة (SL):* `أسفل آخر قاع مكون للهيكل`\n\n"
            f"🛡️ *ميزة تأمين الصفقات:* `بمجرد تحقيق الهدف الأول (TP1)، قم فوراً بنقل وقف الخسارة (SL) إلى سعر الدخول لتأمين الصفقة بالكامل وجعلها خالية من المخاطر!`\n\n"
            f"👑 *إشراف الخبير:* أحمد السيد ({ADMIN_USERNAME})"
        )
        await query.message.edit_text(gold_signal, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "signal_forex":
        forex_signal = (
            f"💶 *[ صفقة فورية مباشرة: العملات الرئيسية EURUSD ]* 💎\n\n"
            f"🏛️ *منصة التنفيذ:* `MT5 Pro`\n"
            f"🌍 *الجلسة والدولة:* `الجلسة الأوروبية (فرانكفورت / لندن)`\n"
            f"⏱️ *الفريم الزمني الناجح:* `ساعة واحدة (1H) و 15 دقيقة`\n\n"
            f"🎯 *تفاصيل الصفقة الاحترافية:*\n"
            f"  🟢 *نوع الإشارة:* `بيع (SELL) عند مناطق الـ Order Block`\n"
            f"  📍 *سعر الدخول (Entry):* `منطقة ارتداد الفالس بريك الحية`\n"
            f"  🎯 *الهدف الأول (TP1):* `جزء من الأرباح السريعة`\n"
            f"  🎯 *الهدف الثاني (TP2):* `استهداف الفراغ السعري`\n"
            f"  🚀 *الهدف الثالث النهائي (TP3):* `الهدف الرئيسي للاتجاه`\n"
            f"  🛑 *وقف الخسارة (SL):* `فوق آخر قمة مظللة`\n\n"
            f"🛡️ *ميزة تأمين الصفقات:* `عند ضرب الهدف الأول (TP1)، انقل الوقف فوراً لسعر الدخول لتأمين أرباحك!`\n\n"
            f"👑 *إشراف الخبير:* أحمد السيد ({ADMIN_USERNAME})"
        )
        await query.message.edit_text(forex_signal, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "signal_crypto":
        crypto_signal = (
            f"🪙 *[ صفقة فورية مباشرة: البيتكوين BTCUSD ]* 💎\n\n"
            f"🏛️ *منصة التنفيذ:* `MT5 / Crypto Exchange`\n"
            f"🌍 *الجلسة والدولة:* `جلسة نيويورك (الولايات المتحدة الأمريكية - تداول رقمي عالي)`\n"
            f"⏱️ *الفريم الزمني الناجح:* `أربع ساعات (4H) و ساعة (1H)`\n\n"
            f"🎯 *تفاصيل الصفقة الاحترافية:*\n"
            f"  🟢 *نوع الإشارة:* `شراء (BUY) تتبع حركة الحيتان`\n"
            f"  📍 *سعر الدخول (Entry):* `منطقة إعادة اختبار الدعم الأسبوعي`\n"
            f"  🎯 *الهدف الأول (TP1):* `الهدف القريب لاختراق المقاومة`\n"
            f"  🚀 *الهدف الثاني النهائي (TP2):* `استهداف القمم التاريخية العالية`\n"
            f"  🛑 *وقف الخسارة (SL):* `إغلاق شمعة أسفل الدعم الرئيسي`\n\n"
            f"🛡️ *ميزة تأمين الصفقات:* `عند الوصول للهدف الأول، قم بتأمين الصفقة برفع الوقف لنقطة الدخول فوراً.`\n\n"
            f"👑 *إشراف الخبير:* أحمد السيد ({ADMIN_USERNAME})"
        )
        await query.message.edit_text(crypto_signal, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "signal_oil":
        oil_signal = (
            f"🛢️ *[ صفقة فورية مباشرة: النفط الخام WTI Oil ]* 💎\n\n"
            f"🏛️ *منصة التنفيذ:* `MT5 Pro Energy`\n"
            f"🌍 *الجلسة والدولة:* `جلسة أمريكا الشمالية وطاقة الأسواق العالمية`\n"
            f"⏱️ *الفريم الزمني الناجح:* `ساعة واحدة (1H) و 30 دقيقة`\n\n"
            f"🎯 *تفاصيل الصفقة الاحترافية:*\n"
            f"  🟢 *نوع الإشارة:* `بيع/شراء حسب التذبذب اللحظي والسيولة`\n"
            f"  📍 *سعر الدخول (Entry):* `منطقة العرض والطلب الكبرى`\n"
            f"  🎯 *الهدف الأول (TP1):* `جني أرباح سريع`\n"
            f"  🚀 *الهدف الثاني النهائي (TP2):* `نهاية امتداد الموجة`\n"
            f"  🛑 *وقف الخسارة (SL):* `إدارة مخاطر ضيقة وآمنة`\n\n"
            f"🛡️ *ميزة تأمين الصفقات:* `تأمين الصفقة إلزامي عند تحقيق الهدف الأول بنقل الوقف لنقطة الدخول.`\n\n"
            f"👑 *إشراف الخبير:* أحمد السيد ({ADMIN_USERNAME})"
        )
        await query.message.edit_text(oil_signal, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    # 3. الاستراتيجيات الثلاثة المحددة حسب الفريمات
    if data == "vip_strategies":
        strat_text = (
            f"⚡ *الاستراتيجيات الثلاثة الحصرية للخبير أحمد السيد:* 💎\n\n"
            f"1️⃣ ⚡ **الاستراتيجية السريعة (السكالبينج):**\n"
            f"   • *الفريم المخصص:* `5 دقائق و 1 دقيقة`\n"
            f"   • *الهدف:* اقتناص النقاط السريعة وسط الجلسات الحية.\n\n"
            f"2️⃣ 📈 **الاستراتيجية القوية (متوسطة المدى):**\n"
            f"   • *الفريم المخصص:* `30 دقيقة و 15 دقيقة`\n"
            f"   • *الهدف:* رصد مناطق الـ Order Block واختراق الفالس بريك.\n\n"
            f"3️⃣ 🏛️ **استراتيجية المدى البعيد (الاستثمارية):**\n"
            f"   • *الفريم المخصص:* `4 ساعات و 1 ساعة`\n"
            f"   • *الهدف:* صيد صفقات صانع السوق الكبرى والاتجاه العام.\n\n"
            f"❖ *اختر أصل التداول من القائمة أو أرسل شارتك لتطبيق التحليل الفوري 👇*"
        )
        await query.message.edit_text(strat_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    # 4. معلومات الدولة والجلسات
    if data == "country_info":
        country_text = (
            f"📍 *معلومات الدولة والجلسات العالمية للتداول:* 🏛️\n\n"
            f"🌐 *نطاق العمل:* الأسواق العالمية والفوركس\n"
            f"💹 *منصة التنفيذ المعتمدة:* `MT5 (MetaTrader 5)`\n"
            f"🌍 *أبرز الجلسات والدول الفعالة:*\n"
            f"   • **جلسة لندن (المملكة المتحدة):** أعلى فوليوم للذهب والعملات.\n"
            f"   • **جلسة نيويورك (الولايات المتحدة):** سيولة ضخمة للبيتكوين والنفط والذهب.\n"
            f"   • **جلسة طوكيو/سيدني (اليابان وأستراليا):** تحركات آسيوية هادئة.\n\n"
            f"❖ *للاشتراك وطلب العضوية الكاملة راسل المطور:* `{ADMIN_USERNAME}` 👑"
        )
        await query.message.edit_text(country_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "enter_key_prompt":
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text(
            "🔑 *تفعيل رخصة العضوية الفاخرة (VIP)*\n\n❖ أرسل كود التفعيل الخاص بك الآن في رسالة نصية لتفعيله فوراً 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_kb)
        )
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
            f"❖ راسل المطور للاشتراك والحصول على كودك الخاص: `{ADMIN_USERNAME}` 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(sub_kb)
        )
        return

    if data == "support":
        await query.message.edit_text(
            f"🛠️ *الدعم الفني للاشتراك والتواصل مع الخبير أحمد السيد*\n\n❖ راسل المطور مباشرة للاشتراك: `{ADMIN_USERNAME}` ⚡",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_kb)
        )
    elif data == "main_menu":
        await start_command(update, context)

# ==================== معالج الرسائل وشارتات الشاشة والفحص الاحترافي ====================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    try:
        user_id = message.from_user.id
        is_admin = (user_id == ADMIN_ID)

        # التحقق من إرسال كود التفعيل النصي
        if message.text and context.user_data.get('waiting_for_key'):
            context.user_data['waiting_for_key'] = False
            entered_key = message.text.strip()
            
            duration_val = db.get_item(f"key_duration_{entered_key}")
            
            if duration_val:
                expiry_time = time.time() + float(duration_val)
                db.set_item(f"expiry_{user_id}", str(expiry_time))
                db.delete_item(f"key_duration_{entered_key}")
                
                await message.reply_text("🎉 *مبارك يا مولاي! تم تفعيل رخصة الـ VIP بنجاح تام.*\nأرسل `/start` للاستمتاع بكافة مزايا النخبة 🚀", parse_mode="Markdown")
            else:
                await message.reply_text("❌ *عذراً، كود التفعيل غير صحيح، منتهي الصلاحية، أو تم استخدامه مسبقاً.*\nراسل المطور للاشتراك: " + ADMIN_USERNAME, parse_mode="Markdown")
            return

        # تحليل سكرين الشاشة (الصورة المرسلة للشارت) بأكثر من استراتيجية وتأمين الصفقة
        if message.photo:
            is_vip = check_user_vip(user_id) or is_admin
            tier_badge = "💎 [VIP Elite Member]" if is_vip else "🔓 [Free Member]"
            
            await message.reply_text(f"⚡ *جاري فحص الشارت وتحليله بأكثر من استراتيجية عبر منصة MT5 {tier_badge}... 📈*", parse_mode="Markdown")
            
            report = (
                f"📊 *[ تقرير التحليل الشامل للشارت - MT5 Pro ]* 💎\n\n"
                f"🏛️ *مصدر التحليل:* `قراءة مباشرة للهيكل، Order Block، وسيولة الحيتان`\n"
                f"🌍 *الجلسة والدولة الحالية:* `جلسة لندن / نيويورك (تداول عالمي)`\n"
                f"⏱️ *الفريم الأنسب للصفقة:* `15 دقيقة / 30 دقيقة`\n\n"
                f"🎯 *مستويات الصفقة المضمونة والمستخرجة:*\n"
                f"  🟢 *نوع الصفقة:* `شراء/بيع (حسب هيكل السكرين المرسل)`\n"
                f"  📍 *سعر الدخول (Entry):* `منطقة الارتداد الدقيقة المستخرجة من الشارت`\n"
                f"  🎯 *الهدف الأول (TP1):* `عند أول مقاومة أو قمة قريبة`\n"
                f"  🎯 *الهدف الثاني (TP2):* `امتداد السيولة المتوسط`\n"
                f"  🚀 *الهدف الثالث النهائي (TP3):* `استهداف القمة الكبرى للصانع`\n"
                f"  🛑 *وقف الخسارة (SL):* `إدارة مخاطر آمنة خلف الهيكل`\n\n"
                f"🛡️ *ميزة تأمين الصفقات:* `فور وصول السعر للهدف الأول (TP1)، قم بتحويل وقف الخسارة (SL) إلى سعر الدخول فوراً لتأمين أرباحك وجعل الصفقة آمنة 100%!`\n\n"
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
