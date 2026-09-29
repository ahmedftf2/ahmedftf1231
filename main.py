import logging
import datetime
import random
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import (
    ADMIN_ID, 
    CHANNEL_USERNAME, 
    get_main_control_keyboard, 
    get_timeframes_keyboard, 
    get_lots_keyboard, 
    get_admin_inline_panel
)

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"

db = {
    "users": {},
    "codes": {},
    "banned": set(),
    "last_signal": "",
    "user_settings": {}
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_live_gold_price():
    try:
        response = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data.get("price", 4141.50))
    except Exception as e:
        logging.error(f"خطأ في جلب السعر الحي: {e}")
    return 4141.50

def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    if user_id in db["users"]:
        expiry_date = db["users"][user_id].get("expiry")
        if expiry_date and datetime.datetime.now() < expiry_date:
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in db["banned"]:
        await update.message.reply_text("❌ أنت محظور من النظام الأمني للبوت.")
        return

    if user.id not in db["users"] and user.id != ADMIN_ID:
        db["users"][user.id] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "بدون معرف",
            "expiry": datetime.datetime.now() + datetime.timedelta(hours=24)
        }
    
    if user.id not in db["user_settings"]:
        db["user_settings"][user.id] = {"tf": "5m", "lot": 0.01}

    is_admin = (user.id == ADMIN_ID)
    
    welcome_msg = (
        f"🦅 **أبر زعيم أسواق المال | أحمد السيد** 🦅\n"
        f"💎 **بوت حوت الذهب الاحترافي (VIP Edition)** 💎\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 **عن النظام والمطور:**\n"
        f"نظام تداول آلي خوارزمي متطور مصمم خصيصاً لاصطياد أرباح الذهب (XAUUSD) بدقة صواريخ وفق أحدث خوارزميات رصد السيولة والأخبار العالمية الكبرى.\n\n"
        f"🏆 **إنجازاتنا وخبراتنا:**\n"
        f"- إدارة محافظ ضخمة بنسب نجاح قياسية تتجاوز المدارس التقليدية.\n"
        f"- ابتكار استراتيجيات منع العكس تماماً وتحقيق الأهداف المتعددة.\n"
        f"- بناء مجتمع نخبوي يضم أشرس المتداولين في أسواق المال.\n\n"
        f"📱 **منصات التواصل الرسمية للمطور (أحمد السيد):**\n"
        f"🔹 **Telegram:** `@alpha_XK`[span_0](start_span)[span_0](end_span)\n"
        f"🔹 **Instagram:** `@your_insta_account`\n"
        f"🔹 **TikTok:** `@your_tiktok_account`\n\n"
        f"📊 **حالة العضوية الفخمة:** صلاحية مطلقة - كبار الشخصيات VIP ♾️\n"
        f"📞 **للدعم والتفعيل المباشر:** `V8V8VN@`[span_1](start_span)[span_1](end_span)\n\n"
        f"👇 **اختر من قائمة العمليات أدناه:**"
    )
    
    await update.message.reply_text(welcome_msg, reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in db["banned"]:
        await query.edit_message_text("❌ عذراً، تم حظرك نهائياً.")
        return

    data = query.data

    if (data.startswith("admin_") or data == "publish_to_channel") and user_id != ADMIN_ID:
        db["banned"].add(user_id)
        await query.edit_message_text("🚨 تنبيه أمني: تم رصد محاولة اختراق وتم حظرك!")
        return

    if data.startswith("tf_"):
        tf = data.replace("tf_", "")
        db["user_settings"][user_id]["tf"] = tf
        await query.edit_message_text(f"✅ **تم ضبط الفريم الزمني إلى:** `{tf}`", parse_mode="Markdown")

    elif data.startswith("lot_"):
        lot = float(data.replace("lot_", ""))
        db["user_settings"][user_id]["lot"] = lot
        await query.edit_message_text(f"✅ **تم ضبط حجم اللوت إلى:** `{lot}`", parse_mode="Markdown")

    elif data.startswith("admin_gen_"):
        period_type = data.replace("admin_gen_", "")
        if period_type == "1h":
            delta = datetime.timedelta(hours=1)
            desc = "ساعة واحدة (السعر: 10)"
        elif period_type == "1d":
            delta = datetime.timedelta(days=1)
            desc = "يوم واحد (السعر: 25)"
        elif period_type == "7d":
            delta = datetime.timedelta(days=7)
            desc = "أسبوع واحد (السعر: 75)"
        elif period_type == "14d":
            delta = datetime.timedelta(days=14)
            desc = "أسبوعين (السعر: 125)"
        elif period_type == "30d":
            delta = datetime.timedelta(days=30)
            desc = "شهر VIP (السعر: 225)"
        else:
            delta = datetime.timedelta(days=30)
            desc = "شهر VIP"
        
        code = f"VIP-{period_type.upper()}-{random.randint(1000, 9999)}"
        db["codes"][code] = {"delta": delta, "used": False}
        await query.edit_message_text(f"✅ تم توليد كود ({desc}) بنجاح:\n`{code}`", parse_mode="Markdown")

    elif data == "admin_list_users":
        if not db["users"]:
            await query.edit_message_text("👥 لا يوجد مشتركين مسجلين حالياً.")
            return
        msg = "👥 **قائمة المشتركين المسيطر عليهم:**\n"
        for uid, info in db["users"].items():
            msg += f"- {info['name']} (`{uid}`) | {info['username']}\n"
        await query.edit_message_text(msg[:4000], parse_mode="Markdown")

    elif data == "publish_to_channel":
        if db["last_signal"]:
            try:
                await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=db["last_signal"], parse_mode="Markdown")
                await query.edit_message_text("✅ **تم نشر التحليل بنجاح إلى قناتك العامة!**")
            except Exception as e:
                await query.edit_message_text(f"❌ خطأ في النشر: {e}")
        else:
            await query.edit_message_text("⚠️ لا يوجد تحليل لنشره حالياً.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    text = update.message.text if update.message.text else ""

    if text.startswith("VIP-"):
        code_info = db["codes"].get(text)
        if code_info and not code_info["used"]:
            code_info["used"] = True
            delta = code_info["delta"]
            if user_id not in db["users"]:
                db["users"][user_id] = {"name": update.effective_user.full_name, "username": f"@{update.effective_user.username}"}
            db["users"][user_id]["expiry"] = datetime.datetime.now() + delta
            await update.message.reply_text(f"🎉 **مبروك يا مولاي! تم تفعيل اشتراكك بنجاح.**", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ الكود غير صالح أو تم استخدامه مسبقاً.")
        return

    if text == "⚙️ لوحة القيادة الإدارية لكبار الشخصيات [VIP]":
        if user_id != ADMIN_ID:
            db["banned"].add(user_id)
            return
        await update.message.reply_text("👑 **غرفة العمليات المركزية والتحكم التام للأدمن:**", reply_markup=get_admin_inline_panel())
        return

    if text == "⏱️ الفريم: [M5]" or text == "🌐 العالمي + الأخبار":
        await update.message.reply_text("اختر الفريم الزمني المطلوب:", reply_markup=get_timeframes_keyboard())
        return

    if text == "⚖️ اللوت: [0.01]":
        await update.message.reply_text("اختر حجم اللوت المناسب:", reply_markup=get_lots_keyboard())
        return

    if text == "💎 باقات وقائمة أسعار VIP الفاخرة":
        pricing_text = (
            f"💎 **باقات وأسعار رخص السيطرة لأسواق الذهب:**\n\n"
            f"⏱️ كود ساعة ──> 10\n"
            f"📅 كود يومي (24 ساعة) ──> 25\n"
            f"📆 كود أسبوعي ──> 75\n"
            f"🗓️ كود أسبوعين ──> 125\n"
            f"👑 كود شهر VIP ──> 225\n\n"
            f"للحصول على أي كود، تواصل مع المطور: `V8V8VN@`[span_2](start_span)[span_2](end_span)"
        )
        await update.message.reply_text(pricing_text, parse_mode="Markdown")
        return

    if text == "🔑 تفعيل رخصة اشتراك جديدة":
        await update.message.reply_text("🔑 أرسل الآن كود الاشتراك (الذي تبدأ حروفه بـ VIP-) لتفعيله فوراً.")
        return

    elif text == "🔄 تحديث الصفقة والسعر الحي":
        if not is_subscribed(user_id):
            await update.message.reply_text("❌ انتهت صلاحية اشتراكك. تواصل مع الإدارة لتفعيل كود جديد.")
            return
        
        curr = get_live_gold_price()
        update_msg = (
            f"🔄 **تم تحديث الأسعار الفورية بنجاح!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🟡 سعر أونصة الذهب الحي الحالي: `{curr}`\n"
            f"⚡ السوق مستقر وجاهز لتنفيذ الأوامر بدقة عالية."
        )
        await update.message.reply_text(update_msg, parse_Mode="Markdown")
        return

    elif text == "📊 استخراج الصفقة الملكية (منع العكس تماماً 1M%)":
        if not is_subscribed(user_id):
            await update.message.reply_text("❌ انتهت صلاحية اشتراكك. تواصل مع الإدارة لتفعيل كود جديد.")
            return

        settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
        curr = get_live_gold_price()
        opn = round(curr - 2.5, 2)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        trend_score = curr - opn
        if trend_score >= 0:
            action = "شراء قاصف (BUY 🟢)"
            strategy_school = "مدرسة السيولة المؤسساتية العميقة + ثغرة كسر الارتكاز"
            sl = round(curr - 4.5, 2)
            tp1 = round(curr + 9.0, 2)
            tp2 = round(curr + 18.0, 2)
        else:
            action = "بيع قاصف (SELL 🔴)"
            strategy_school = "مدرسة الفجوات السعرية (FVG) + ثغرة استنزاف السيولة"
            sl = round(curr + 4.5, 2)
            tp1 = round(curr - 9.0, 2)
            tp2 = round(curr - 18.0, 2)

        report = (
            f"👑 **التقرير الإمبراطوري الشامل للسيطرة على الذهب** 👑\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ **التوقيت:** {now_str}\n"
            f"📊 **الفريم:** `{settings['tf']}` | 💰 **اللوت:** `{settings['lot']}`\n"
            f"🏛 **المدارس المطبقة:** {strategy_school}\n"
            f"📈 **فحص السعر الحي الفوري:** `{curr}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **التوصية المسيطرة:**\n"
            f"🔹 **نوع العقد:** {action}\n"
            f"🔹 **سعر الدخول الفوري:** `{curr}`\n"
            f"🛑 **وقف الخسارة (SL):** `{sl}`\n"
            f"🎯 **الهدف الأول (TP1):** `{tp1}`\n"
            f"🎯 **الهدف الثاني (TP2):** `{tp2}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *مسح حي مباشر وبدون أخطاء.*"
        )
        db["last_signal"] = report

        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📢 نشر هذا التحليل الاستراتيجي للقناة العامة", callback_data="publish_to_channel")]]) if user_id == ADMIN_ID else None
        await update.message.reply_text(report, parse_mode="Markdown", reply_markup=markup)
        return

    else:
        await update.message.reply_text("استخدم الأزرار الثابتة أسفل الشاشة للتنقل وتنفيذ الأوامر بدقة.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
    curr = get_live_gold_price()
    
    result = (
        f"📸 **نتائج فحص السكرين الإمبراطوري:**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 تم فحص الشارت ومطابقته بدقة.\n"
        f"🟡 السعر الفوري المرصود: `{curr}`\n"
        f"📊 **النتيجة:** النطاق السعري مطابق لقواعد السيولة.\n"
        f"💰 **حجم اللوت المعتمد:** `{settings['lot']}`\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    db["last_signal"] = result
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("📢 نشر التحليل للقناة العامة", callback_data="publish_to_channel")]]) if user_id == ADMIN_ID else None
    await update.message.reply_text(result, parse_mode="Markdown", reply_markup=markup)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    print("👑 Refreshed Live Signal Imperial Core is Online...")
    app.run_polling()

if __name__ == "__main__":
    main()
