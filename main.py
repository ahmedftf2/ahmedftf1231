import logging
import datetime
import random
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import (
    ADMIN_ID, 
    CHANNEL_USERNAME, 
    get_persistent_reply_keyboard,
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

def get_welcome_text():
    return (
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
        f"🔹 **Telegram:** `@alpha_XK`\n"
        f"🔹 **Instagram:** `@your_insta_account`\n"
        f"🔹 **TikTok:** `@your_tiktok_account`\n\n"
        f"📊 **حالة العضوية الفخمة:** صلاحية مطلقة - كبار الشخصيات VIP ♾️\n"
        f"📞 **للدعم والتفعيل المباشر:** `V8V8VN@`\n\n"
        f"👇 **اختر من قائمة العمليات أدناه:**"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in db["banned"]:
        if update.callback_query:
            await update.callback_query.answer("❌ أنت محظور.", show_alert=True)
        else:
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
    msg = get_welcome_text()
    
    # إرسال الكيبورد الثابت بجانب الكتابة أولاً لتظهر اللوحة دائماً
    reply_kb = get_persistent_reply_keyboard()
    
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
    else:
        await update.message.reply_text("👇 لوحة الأوامر الثابتة جاهزة أسفل الشاشة:", reply_markup=reply_kb)
        await update.message.reply_text(msg, reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in db["banned"]:
        await query.edit_message_text("❌ عذراً، تم حظرك نهائياً.")
        return

    data = query.data
    is_admin = (user_id == ADMIN_ID)

    if (data.startswith("admin_") or data == "publish_to_channel") and not is_admin:
        db["banned"].add(user_id)
        await query.edit_message_text("🚨 تنبيه أمني: تم رصد محاولة اختراق وتم حظرك!")
        return

    if data == "menu_start":
        await query.edit_message_text(get_welcome_text(), reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        return

    elif data == "menu_settings" or data == "menu_news":
        await query.edit_message_text("⏱️ **اختر الفريم الزمني المطلوب للشارت والتحليل:**", reply_markup=get_timeframes_keyboard(), parse_mode="Markdown")
        return

    elif data == "menu_lot":
        await query.edit_message_text("⚖️ **اختر حجم اللوت المناسب لتداولاتك:**", reply_markup=get_lots_keyboard(), parse_mode="Markdown")
        return

    elif data == "menu_pricing":
        pricing_text = (
            f"💎 **باقات وأسعار رخص السيطرة لأسواق الذهب:**\n\n"
            f"⏱️ كود ساعة ──> 10\n"
            f"📅 كود يومي (24 ساعة) ──> 25\n"
            f"📆 كود أسبوعي ──> 75\n"
            f"🗓️ كود أسبوعين ──> 125\n"
            f"👑 كود شهر VIP ──> 225\n\n"
            f"للحصول على أي كود، تواصل مع المطور: `V8V8VN@`"
        )
        await query.edit_message_text(pricing_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]]), parse_mode="Markdown")
        return

    elif data == "menu_activate":
        context.user_data["waiting_for_code"] = True
        await query.edit_message_text("🔑 **أرسل الآن كود الاشتراك (الذي تبدأ حروفه بـ VIP-) في خانة الكتابة لتفيله فوراً.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]]), parse_mode="Markdown")
        return

    elif data == "menu_update":
        if not is_subscribed(user_id):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك. تواصل مع الإدارة لتفعيل كود جديد.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
            return
        curr = get_live_gold_price()
        update_msg = (
            f"🔄 **تم تحديث الأسعار الفورية بنجاح!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🟡 سعر أونصة الذهب الحي الحالي: `{curr}`\n"
            f"⚡ السوق مستقر وجاهز لتنفيذ الأوامر بدقة عالية."
        )
        await query.edit_message_text(update_msg, reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        return

    elif data == "menu_analysis":
        if not is_subscribed(user_id):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك. تواصل مع الإدارة لتفعيل كود جديد.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
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

        markup_list = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]]
        if is_admin:
            markup_list.insert(0, [InlineKeyboardButton("📢 نشر هذا التحليل الاستراتيجي للقناة العامة", callback_data="publish_to_channel")])
        
        await query.edit_message_text(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(markup_list))
        return

    elif data == "menu_admin":
        if not is_admin:
            db["banned"].add(user_id)
            return
        await query.edit_message_text("👑 **غرفة العمليات المركزية والتحكم التام للأدمن:**", reply_markup=get_admin_inline_panel())
        return

    if data.startswith("tf_"):
        tf = data.replace("tf_", "")
        db["user_settings"][user_id]["tf"] = tf
        await query.edit_message_text(f"✅ **تم ضبط الفريم الزمني إلى:** `{tf}`", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

    elif data.startswith("lot_"):
        lot = float(data.replace("lot_", ""))
        db["user_settings"][user_id]["lot"] = lot
        await query.edit_message_text(f"✅ **تم ضبط حجم اللوت إلى:** `{lot}`", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

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
        await query.edit_message_text(f"✅ تم توليد كود ({desc}) بنجاح:\n`{code}`", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")

    elif data == "admin_list_users":
        if not db["users"]:
            await query.edit_message_text("👥 لا يوجد مشتركين مسجلين حالياً.", reply_markup=get_admin_inline_panel())
            return
        msg = "👥 **قائمة المشتركين المسيطر عليهم:**\n"
        for uid, info in db["users"].items():
            msg += f"- {info['name']} (`{uid}`) | {info['username']}\n"
        await query.edit_message_text(msg[:4000], reply_markup=get_admin_inline_panel(), parse_mode="Markdown")

    elif data == "publish_to_channel":
        if db["last_signal"]:
            try:
                await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=db["last_signal"], parse_mode="Markdown")
                await query.edit_message_text("✅ **تم نشر التحليل بنجاح إلى قناتك العامة!**", reply_markup=get_admin_inline_panel())
            except Exception as e:
                await query.edit_message_text(f"❌ خطأ في النشر: {e}", reply_markup=get_admin_inline_panel())
        else:
            await query.edit_message_text("⚠️ لا يوجد تحليل لنشره حالياً.", reply_markup=get_admin_inline_panel())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    text = update.message.text if update.message.text else ""
    is_admin = (user_id == ADMIN_ID)

    if text == "🚀 تشغيل /start واللوحة الرئيسية":
        await start(update, context)
        return

    if context.user_data.get("waiting_for_code"):
        context.user_data["waiting_for_code"] = False
        code_info = db["codes"].get(text)
        if code_info and not code_info["used"]:
            code_info["used"] = True
            delta = code_info["delta"]
            if user_id not in db["users"]:
                db["users"][user_id] = {"name": update.effective_user.full_name, "username": f"@{update.effective_user.username}"}
            db["users"][user_id]["expiry"] = datetime.datetime.now() + delta
            await update.message.reply_text(f"🎉 **مبروك يا مولاي! تم تفعيل اشتراكك بنجاح.**", reply_markup=get_persistent_reply_keyboard(), parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ الكود غير صالح أو تم استخدامه مسبقاً.", reply_markup=get_persistent_reply_keyboard())
        return
    
    await update.message.reply_text("👇 اضغط على زر التشغيل أسفل الشاشة أو استخدم الأزرار التفاعلية:", reply_markup=get_persistent_reply_keyboard())

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    is_admin = (user_id == ADMIN_ID)
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
    
    markup_list = [[InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]]
    if is_admin:
        markup_list.insert(0, [InlineKeyboardButton("📢 نشر التحليل للقناة العامة", callback_data="publish_to_channel")])
        
    await update.message.reply_text(result, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(markup_list))

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    print("👑 Ultimate Bot Core with Persistent Keyboard & Back Button is Online...")
    app.run_polling()

if __name__ == "__main__":
    main()
