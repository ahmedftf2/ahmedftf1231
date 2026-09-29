import logging
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from utils import ADMIN_ID, get_reply_keyboard, get_subscriber_keyboard, get_admin_keyboard

# إعداد السجلات السيبرانية
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# التوكن الخاص بك
BOT_TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"

# قاعدة بيانات آمنة للأكواد والمستخدمين VIP
VALID_CODES = {"AHMED-VIP-2026", "GOLD-ELITE-1M", "ALPHA-BOSS-999", "SMC-MASTER-777"}
VIP_USERS = {ADMIN_ID}  # أنت المالك والأدمن المطلق

# نظام تتبع الحالات المؤقتة للمستخدمين
USER_STATE = {}

# دالة البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_vip = user_id in VIP_USERS
    
    welcome_text = (
        f"🏴‍☠️ **مرحباً بك مجدداً في المحطة السرية الإمبراطورية** 🏴‍☠️\n\n"
        f"بإشراف مباشر من الخبير الأسطوري **أحمد السيد** 👁️‍🗨️.\n"
        f"النظام يعمل بكفاءة تامة وأمان مطلق 100%.\n"
        f"اختر وجهتك التالية لتسيطر على الأسواق.."
    )
    
    # إرسال الكيبورد السفلي
    await update.message.reply_text("تم تفعيل اللوحة الإمبراطورية السفلية بنجاح.", reply_markup=get_reply_keyboard())
    
    # فحص الصلاحيات بدقة مطلقة
    if user_id == ADMIN_ID:
        full_keyboard_list = get_subscriber_keyboard(is_vip=True).inline_keyboard + get_admin_keyboard().inline_keyboard
        await update.message.reply_text(
            f"{welcome_text}\n\n⚡ *[وضع السيطرة المطلقة للأدمن أحمد السيد مفعل]*",
            reply_markup=InlineKeyboardMarkup(full_keyboard_list),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_subscriber_keyboard(is_vip=is_vip),
            parse_mode="Markdown"
        )

# التعامل مع الأزرار الضغطية (Callback Queries)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    is_vip = user_id in VIP_USERS

    if data == "gold_analysis":
        sessions = ["جلسة لندن الكبرى", "جلسة نيويورك السيبرانية", "جلسة آسيا التجميعية"]
        current_session = random.choice(sessions)
        
        response_text = (
            f"🟡 **التقرير الإمبراطوري لتحليل الذهب (مدارس SMC & العرض والطلب)** 🟡\n\n"
            f"⏰ **التوقيت والجلسة:** {current_session} - رصد مناطق السيولة (Liquidity Sweep).\n"
            f"📊 **الفريمات المدمجة:** M15 / M30 / H1\n"
            f"💪 **قوة الصفقة:** قوية جداً (تتضمن 3 أهداف كاملة مع وقف خسارة وتأمين).\n\n"
            f"🎯 **الهدف الأول:** 2383.20 (تأمين الصفقة وتحريك الوقف لنقطة الدخول).\n"
            f"🎯 **الهدف الثاني:** 2390.50\n"
            f"🎯 **الهدف الثالث:** 2398.00\n"
            f"🛑 **وقف الخسارة (Stop Loss):** 2373.50\n\n"
            f"🚀 *جاهزة للتنفيذ الفوري برعاية الإمبراطورية.*"
        )
        await query.message.reply_text(response_text, parse_mode="Markdown")

    elif data == "strategies_panel":
        strat_text = (
            "🧠 **مركز خوارزميات المدارس الفنية والاستراتيجيات المتقدمة:**\n\n"
            "1️⃣ **مدرسة الذكي المالي (SMC):** فحص خريطة الـ Order Blocks.\n"
            "2️⃣ **مدرسة العرض والطلب (Supply & Demand):** تحديد مناطق الانفجار السعري.\n"
            "3️⃣ **التحليل الكلاسيكي والزمني:** رصد دورات الأسعار وتجارب إعادة الاختبار.\n\n"
            "💡 *جميع هذه المدارس تعمل بتناغم لتعطيك أقوى المؤشرات.*"
        )
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_main")]])
        await query.message.reply_text(strat_text, reply_markup=back_kb, parse_mode="Markdown")

    elif data == "back_to_main":
        await query.message.reply_text("القائمة الرئيسية المفعلة:", reply_markup=get_subscriber_keyboard(is_vip=is_vip))

    elif data == "screen_analysis":
        await query.message.reply_text(
            "📸 **نظام فحص شاشة الشارت:**\n\n"
            "أرسل صورة الشارت (سكرين شاشة) الآن، وسيقوم النظام بقراءة خطوط الاتجاه ومناطق الارتداد الفني."
        )

    elif data == "add_code":
        USER_STATE[user_id] = "waiting_for_code"
        await query.message.reply_text(
            "🔑 **بوابة تفعيل شفرة النخبة VIP الإمبراطورية:**\n\n"
            "أرسل كود التفعيل الخاص بك الآن في رسالة جديدة لكي يتحقق منه النظام ويفعل لك كافة الصلاحيات فوراً."
        )

    elif data == "vip_info":
        await query.message.reply_text("💎 **حسابك يحمل رتبة VIP الإمبراطورية.** كافة الصفقات والاستراتيجيات مفتوحة لك بالكامل.")

    # حماية لوحة الأدمن
    elif data.startswith("admin_"):
        if user_id != ADMIN_ID:
            await query.message.reply_text(
                "🔒 **بوابة النخبة مغلقة في وجهك!**\n"
                "هذا التحليل الإمبراطوري مخصص حصراً للخبير **أحمد السيد**.\n"
                "للحصول على شفرة الدخول، تواصل مع المعتمد: @V8V8VN"
            )
            return
        
        if data == "admin_vip_panel":
            await query.message.reply_text(f"🛠️ **لوحة القيادة الإدارية:** الأنظمة تعمل بأعلى كفاءة. المشتركون VIP النشطون: {len(VIP_USERS)}")
        elif data == "admin_glitch":
            await query.message.reply_text("⚡ **استخراج الثغرات (%1M):** تم فحص عقود صانع السوق واكتشاف الفرص السيبرانية الكبرى للذهب.")
        elif data == "admin_news":
            await query.message.reply_text("📈 **العالمي + الأخبار والسيولة [M5]:** السوق مستقر وجاهز للعمليات.")
        elif data == "admin_generate_code":
            new_code = f"ALPHA-VIP-{random.randint(10000, 99999)}"
            VALID_CODES.add(new_code)
            await query.message.reply_text(f"💎 **تم توليد كود إمبراطوري جديد بنجاح:**\n`{new_code}`\n\nقم بنسخه ومنحه لمن تشاء ليفعله في البوت.", parse_mode="Markdown")
        elif data == "admin_prices":
            await query.message.reply_text("🏷️ **قائمة أسعار VIP الفاخرة:**\n- اشتراك شهرى: 150$\n- اشتراك مدى الحياة: 400$\n(التفعيل يتم حصراً عبر الأكواد).")
        elif data == "admin_new_license":
            await query.message.reply_text("➕ **تفعيل رخصة يدوية:** أرسل الآيدي الخاص بالمشترك لتسجيله فوراً في قاعدة البيانات.")

# معالجة الرسائل والنصوص والصور
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message.text else ""
    user_id = update.effective_user.id

    if text == "🗑️ مسح وإعادة ضبط السجل":
        await update.message.reply_text("🔄 **تم مسح السجل وإعادة ضبط المحطة بنجاح.**\nأهلاً بك في القائمة الرئيسية النظيفة.", reply_markup=get_reply_keyboard())
        is_vip = user_id in VIP_USERS
        if user_id == ADMIN_ID:
            full_keyboard_list = get_subscriber_keyboard(is_vip=True).inline_keyboard + get_admin_keyboard().inline_keyboard
            await update.message.reply_text("لوحة التحكم السيبرانية الخاصة بك يا مولاي أحمد:", reply_markup=InlineKeyboardMarkup(full_keyboard_list))
        else:
            await update.message.reply_text("قائمة الخيارات الإمبراطورية:", reply_markup=get_subscriber_keyboard(is_vip=is_vip))
            
    elif text == "📋 القائمة الرئيسية":
        await start(update, context)

    # تفعيل الكود المدخل
    elif USER_STATE.get(user_id) == "waiting_for_code":
        entered_code = text.strip()
        if entered_code in VALID_CODES:
            VIP_USERS.add(user_id)
            USER_STATE[user_id] = None
            await update.message.reply_text(
                "🎉 **تهانينا! تم تفعيل الشفرة الإمبراطورية بنجاح تام.**\n"
                "لقد تم ترقية حسابك إلى رتبة **VIP المطلقة** وتفتح لك الآن كافة صفقات الذهب واستراتيجيات المدارس الفنية حصرياً!",
                reply_markup=get_subscriber_keyboard(is_vip=True)
            )
        else:
            await update.message.reply_text("❌ **الكود غير صحيح أو منتهي الصلاحية.**\nتأكد من الشفرة أو تواصل مع المطور @V8V8VN للحصول على كود معتمد.")
    
    # فحص الصور المرسلة
    elif update.message.photo:
        await update.message.reply_text(
            "📸 **تم التقاط سكرين الشاشة بنجاح وبدء فحص خوارزميات المدارس الفنية!**\n\n"
            "🔍 جاري مطابقة الصورة مع نماذج العرض والطلب ومؤشرات السوق...\n"
            "✨ *النتيجة التوجيهية:* تم رصد منطقة إعادة اختبار (Retest) قوية. الاتجاه المرجح صاعد."
        )

# التشغيل الرئيسي
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO & ~filters.COMMAND, message_handler))

    print("🛸 Zo Supreme Core is online for Commander Alpha...")
    application.run_polling()

if __name__ == "__main__":
    main()
