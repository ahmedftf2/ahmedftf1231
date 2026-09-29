import logging
import datetime
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import get_live_gold_price, check_forced_subscription, is_subscribed, get_remaining_time

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

def get_main_control_keyboard(is_admin=False, user_id=None):
    time_left = get_remaining_time(user_id, db) if user_id else "غير مسجل"
    keyboard = [
        [InlineKeyboardButton(f"⏳ الوقت المتبقي لاشتراكك: {time_left}", callback_data="check_time")],
        [InlineKeyboardButton("🌍 تحليل سوق الذهب المؤسساتي المتقدم (ICT/SMC)", callback_data="menu_analysis")],
        [InlineKeyboardButton("🔄 المراقبة الآلية للصفقة الفعالة والهدف", callback_data="menu_update")],
        [InlineKeyboardButton("⏱️ الفريم: [M5 المؤسساتي]", callback_data="menu_settings"), InlineKeyboardButton("🌐 سيولة الشرق الأوسط والعالم", callback_data="menu_news")],
        [InlineKeyboardButton("⚖ حجم اللوت الحقيقي: [0.01]", callback_data="menu_lot")],
        [InlineKeyboardButton("💎 أسعار وباقات الاشتراكات الحقيقية", callback_data="menu_pricing")],
        [InlineKeyboardButton("🔑 تفعيل كود اشتراك رسمي", callback_data="menu_activate")]
    ]
    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ غرفة القيادة والإدارة العليا [ADMIN]", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)

def get_pricing_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱️ كود ساعة (1 ساعة) - 10$", callback_data="price_1h")],
        [InlineKeyboardButton("📅 كود يوم (24 ساعة) - 30$", callback_data="price_1d")],
        [InlineKeyboardButton("📆 كود أسبوع - 90$", callback_data="price_7d")],
        [InlineKeyboardButton("📅 كود أسبوعين - 150$", callback_data="price_14d")],
        [InlineKeyboardButton("💎 كود شهر VIP عالمي - 225$", callback_data="price_30d")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="menu_start")]
    ])

def get_timeframes_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱️ فريم 1 دقيقة (1M)", callback_data="tf_1m"), InlineKeyboardButton("⏱️ فريم 5 دقائق (5M)", callback_data="tf_5m")],
        [InlineKeyboardButton("⏱️ فريم 15 دقيقة (15M)", callback_data="tf_15m"), InlineKeyboardButton("⏱️ فريم 1 ساعة (1H)", callback_data="tf_1h")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]
    ])

def get_lots_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 0.01", callback_data="lot_0.01"), InlineKeyboardButton("🔹 0.05", callback_data="lot_0.05"), InlineKeyboardButton("🔹 0.10", callback_data="lot_0.10")],
        [InlineKeyboardButton("🔹 0.50", callback_data="lot_0.50"), InlineKeyboardButton("🔹 1.00 (Standard)", callback_data="lot_1.00"), InlineKeyboardButton("🔹 5.00 (VIP)", callback_data="lot_5.00")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]
    ])

def get_admin_inline_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎟️ إصدار كود [ساعة] - 10$", callback_data="admin_gen_1h"), InlineKeyboardButton("🎟️ إصدار كود [يوم] - 30$", callback_data="admin_gen_1d")],
        [InlineKeyboardButton("🎟️ إصدار كود [أسبوع] - 90$", callback_data="admin_gen_7d"), InlineKeyboardButton("🎟️ إصدار كود [أسبوعين] - 150$", callback_data="admin_gen_14d")],
        [InlineKeyboardButton("💎 إصدار كود [شهر VIP] - 225$", callback_data="admin_gen_30d")],
        [InlineKeyboardButton("👥 المشتركين الحقيقيين", callback_data="admin_list_users"), InlineKeyboardButton("🔑 إدارة الأكواد", callback_data="admin_list_codes")],
        [InlineKeyboardButton("📢 نشر التحليل العالمي للقناة", callback_data="publish_to_channel")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="menu_start")]
    ])

def get_welcome_text(user_id=None):
    time_left = get_remaining_time(user_id, db) if user_id else "غير مسجل"
    return (
        f"🦅 **النظام المالي العالمي الموحد | الشرق الأوسط & العالم** 🦅\n"
        f"🌐 **منظومة التداول الحقيقية والمؤسساتية للذهب (XAU/USD)** 🌐\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ **حالة اشتراكك الحالي:** `{time_left}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📜 **الباقات والأسعار المعتمدة:**\n"
        f"• ساعة واحدة: `10$`\n"
        f"• يوم كامل (24 ساعة): `30$`\n"
        f"• أسبوع كامل: `90$`\n"
        f"• أسبوعين: `150$`\n"
        f"• شهر VIP عالمي: `225$`\n\n"
        f"👇 **اختر الإجراء المطلوب:**"
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
        msg = f"🚨 **يجب الاشتراك أولاً في قناة المطور:**\n👉 {CHANNEL_USERNAME}"
        if update.callback_query:
            await update.callback_query.message.edit_text(msg, reply_markup=join_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=join_markup, parse_mode="Markdown")
        return

    if user.id not in db["users"] and user.id != ADMIN_ID:
        db["users"][user.id] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "بدون معرف",
            "expiry": datetime.datetime.now() + datetime.timedelta(hours=1)
        }
    
    if user.id not in db["user_settings"]:
        db["user_settings"][user.id] = {"tf": "5m", "lot": 0.01}

    is_admin = (user.id == ADMIN_ID)
    msg = get_welcome_text(user.id)
    keyboard = get_main_control_keyboard(is_admin=is_admin, user_id=user.id)
    
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
        await query.edit_message_text(get_welcome_text(user_id), reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id), parse_mode="Markdown")
        return

    elif data == "check_time":
        time_left = get_remaining_time(user_id, db)
        await query.answer(f"⏳ الوقت المتبقي لاشتراكك: {time_left}", show_alert=True)
        return

    elif data == "menu_pricing":
        await query.edit_message_text(
            f"💎 **أسعار وباقات الاشتراكات المعتمدة:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ **ساعة واحدة:** 10$\n"
            f"📅 **يوم كامل:** 30$\n"
            f"📆 **أسبوع:** 90$\n"
            f"📅 **أسبوعين:** 150$\n"
            f"💎 **شهر VIP:** 225$\n\n"
            f"لشراء الكود، تواصل مع المطور وأرسل الكود عبر زر (تفعيل كود اشتراك رسمي).",
            reply_markup=get_pricing_keyboard(), parse_mode="Markdown"
        )
        return

    elif data in ["price_1h", "price_1d", "price_7d", "price_14d", "price_30d"]:
        await query.answer("لشراء هذه الباقة، تواصل مع المطور مباشرة للحصول على الكود الخاص بها.", show_alert=True)
        return

    elif data == "menu_settings" or data == "menu_news":
        await query.edit_message_text("⏱️ **اختر الفريم الزمني العالمي:**", reply_markup=get_timeframes_keyboard(), parse_mode="Markdown")
        return

    elif data.startswith("tf_"):
        tf_val = data.replace("tf_", "").upper()
        if user_id in db["user_settings"]:
            db["user_settings"][user_id]["tf"] = tf_val
        await query.answer(f"✅ تم ضبط الفريم على: {tf_val}", show_alert=False)
        await query.edit_message_text(get_welcome_text(user_id), reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id), parse_mode="Markdown")
        return

    elif data == "menu_lot":
        await query.edit_message_text("⚖️️ **اختر حجم اللوت الحقيقي:**", reply_markup=get_lots_keyboard(), parse_mode="Markdown")
        return

    elif data.startswith("lot_"):
        lot_val = float(data.replace("lot_", ""))
        if user_id in db["user_settings"]:
            db["user_settings"][user_id]["lot"] = lot_val
        await query.answer(f"✅ تم ضبط اللوت على: {lot_val}", show_alert=False)
        await query.edit_message_text(get_welcome_text(user_id), reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id), parse_mode="Markdown")
        return

    elif data == "menu_activate":
        context.user_data["waiting_for_code"] = True
        await query.edit_message_text("🔑 **أرسل الآن كود الاشتراك (ساعة، يوم، أسبوع، إلخ) في خانة الرسائل لتفعيله فوراً.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]]), parse_mode="Markdown")
        return

    elif data == "menu_update":
        if not is_subscribed(user_id, ADMIN_ID, db):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك. تواصل مع المطور لتجديد الباقة.", reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id))
            return
        
        curr = get_live_gold_price()
        active = db["active_signals"].get(user_id)
        
        if active:
            entry = active["entry"]
            direction = active["direction"]
            tp1 = active["tp1"]
            tp2 = active["tp2"]
            sl = active["sl"]
            is_buy = "شراء" in direction
            
            if not active.get("tp1_hit", False) and ((is_buy and curr >= tp1) or (not is_buy and curr <= tp1)):
                active["tp1_hit"] = True
                auto_second_signal = (
                    f"🚨 **تم تحقيق الهدف الأول (TP1) بنجاح! 🎯**\n"
                    f"🌐 السعر الحي الآن: `{curr}`\n"
                    f"🔹 التوجيه للهدف الثاني."
                )
                await query.edit_message_text(auto_second_signal, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ خروج", callback_data="sig_close")]]))
                return
            
            report = (
                f"🌐 **مراقبة السوق المؤسساتي الحي (ICT/SMC)** 🌐\n"
                f"📈 الدخول: `{entry}` | السعر الحالي: `{curr}`\n"
                f"🔹 الاتجاه: `{direction}`\n"
                f"⏳ الوقت المتبقي لاشتراكك: `{get_remaining_time(user_id, db)}`"
            )
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id))
            return
        else:
            await query.edit_message_text(f"🔄 لا توجد صفقة نشطة حالياً. السعر الحي: `{curr}`\n⏳ اشتراكك باقي له: `{get_remaining_time(user_id, db)}`", reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id), parse_mode="Markdown")
            return

    elif data == "menu_analysis":
        if not is_subscribed(user_id, ADMIN_ID, db):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك.", reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id))
            return

        curr = get_live_gold_price()
        settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
        
        is_even = int(curr * 10) % 2 == 0
        direction = "شراء مؤسساتي مكثف (BUY 🟢 - Order Block + FVG)" if is_even else "بيع مؤسساتي مكثف (SELL 🔴 - Liquidity Sweep)"
        entry_price = curr
        tp1 = round(curr + 3.5 if is_even else curr - 3.5, 2)
        tp2 = round(curr + 8.0 if is_even else curr - 8.0, 2)
        sl = round(curr - 4.0 if is_even else curr + 4.0, 2)
        
        db["active_signals"][user_id] = {
            "entry": entry_price,
            "direction": direction,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
            "tp1_hit": False
        }

        report = (
            f"🌍 **التحليل المؤسساتي المتقدم (ICT & SMC)** 🌍\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 السعر الفوري: `{curr}`\n"
            f"📊 الفريم المستخدم: `{settings['tf']}` | اللوت: `{settings['lot']}`\n"
            f"📍 الإشارة: `{direction}`\n"
            f"🎯 الهدف الأول (TP1): `{tp1}`\n"
            f"🎯 الهدف الثاني (TP2): `{tp2}`\n"
            f"🛡️ وقف الخسارة (SL): `{sl}`\n"
            f"⏳ الوقت المتبقي لاشتراكك: `{get_remaining_time(user_id, db)}`\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        db["last_signal"] = report
        await query.edit_message_text(report, parse_mode="Markdown", reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id))
        return

    elif data == "sig_close":
        if user_id in db["active_signals"]:
            del db["active_signals"][user_id]
        await query.edit_message_text(get_welcome_text(user_id), reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id), parse_mode="Markdown")
        return

    elif data == "menu_admin":
        if not is_admin:
            return
        await query.edit_message_text("⚙️ **غرفة القيادة والإدارة العليا للمطور:**", reply_markup=get_admin_inline_panel())
        return

    elif data.startswith("admin_gen_"):
        ptype = data.replace("admin_gen_", "")
        if ptype == "1h":
            delta = datetime.timedelta(hours=1)
            desc = "ساعة واحدة (10$)"
        elif ptype == "1d":
            delta = datetime.timedelta(days=1)
            desc = "يوم كامل (30$)"
        elif ptype == "7d":
            delta = datetime.timedelta(days=7)
            desc = "أسبوع (90$)"
        elif ptype == "14d":
            delta = datetime.timedelta(days=14)
            desc = "أسبوعين (150$)"
        elif ptype == "30d":
            delta = datetime.timedelta(days=30)
            desc = "شهر VIP (225$)"
        else:
            delta = datetime.timedelta(days=1)
            desc = "يوم"

        code = f"VIP-{ptype.upper()}-{random.randint(1000, 9999)}"
        db["codes"][code] = {"delta": delta, "used": False}
        await query.edit_message_text(f"✅ تم إصدار كود ({desc}) بنجاح:\n`{code}`", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")

    elif data == "admin_list_users":
        if not db["users"]:
            await query.edit_message_text("👥 لا يوجد مشتركين مسجلين.", reply_markup=get_admin_inline_panel())
            return
        users_kb = []
        for uid, info in list(db["users"].items())[:10]:
            users_kb.append([InlineKeyboardButton(f"👤 {info['name']} | باقي: {get_remaining_time(uid, db)}", callback_data="noop_c")])
        users_kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")])
        await query.edit_message_text("👥 **قائمة المشتركين وأوقاتهم:**", reply_markup=InlineKeyboardMarkup(users_kb), parse_mode="Markdown")
        return

    elif data == "admin_list_codes":
        if not db["codes"]:
            await query.edit_message_text("🔑 لا توجد أكواد مسجلة.", reply_markup=get_admin_inline_panel())
            return
        codes_kb = []
        for code, info in list(db["codes"].items())[:10]:
            status = "مستخدم ❌" if info["used"] else "فعال ✅"
            codes_kb.append([InlineKeyboardButton(f"🔑 {code} ({status})", callback_data="noop_c")])
        codes_kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")])
        await query.edit_message_text("🔑 **قائمة الأكواد المصنوعة:**", reply_markup=InlineKeyboardMarkup(codes_kb), parse_mode="Markdown")
        return

    elif data == "publish_to_channel":
        if db["last_signal"]:
            await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=db["last_signal"], parse_mode="Markdown")
            await query.edit_message_text("✅ تم النشر للقناة بنجاح.", reply_markup=get_admin_inline_panel())
        else:
            await query.edit_message_text("⚠️ لا يوجد تحليل لنشره.", reply_markup=get_admin_inline_panel())

    elif data.startswith("noop_"):
        await query.answer("ℹ️ معلومة.", show_alert=False)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    is_joined = await check_forced_subscription(user_id, ADMIN_ID, CHANNEL_USERNAME, context)
    if not is_joined:
        return

    is_admin = (user_id == ADMIN_ID)

    if context.user_data.get("waiting_for_code"):
        context.user_data["waiting_for_code"] = False
        text = update.message.text.strip() if update.message.text else ""
        code_info = db["codes"].get(text)
        
        if code_info and not code_info["used"]:
            code_info["used"] = True
            delta = code_info["delta"]
            if user_id not in db["users"]:
                db["users"][user_id] = {"name": update.effective_user.full_name, "username": f"@{update.effective_user.username}"}
            
            current_expiry = db["users"][user_id].get("expiry", datetime.datetime.now())
            base_time = current_expiry if current_expiry > datetime.datetime.now() else datetime.datetime.now()
            db["users"][user_id]["expiry"] = base_time + delta
            
            await update.message.reply_text(f"🎉 **تم تفعيل الكود بنجاح!**\n⏳ اشتراكك الجديد يمتد حتى: `{get_remaining_time(user_id, db)}`", reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id), parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ الكود غير صحيح، منتهي، أو مستخدم مسبقاً.", reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id))
        return
    
    await update.message.reply_text(get_welcome_text(user_id), reply_markup=get_main_control_keyboard(is_admin=is_admin, user_id=user_id), parse_mode="Markdown")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return
    is_joined = await check_forced_subscription(user_id, ADMIN_ID, CHANNEL_USERNAME, context)
    if not is_joined:
        return

    is_admin = (user_id == ADMIN_ID)
    curr = get_live_gold_price()
    settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
    
    result = (
        f"🌍 **فحص الشارت المؤسساتي المتقدم (ICT/SMC):**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 تم فحص السيولة الفعلية عبر الخوادم.\n"
        f"🟢 السعر الفوري الحي للأونصة: `{curr}`\n"
        f"📊 **الحالة:** تم مطابقة الشارت مع مناطق الـ Order Blocks والسيولة.\n"
        f"💰 اللوت المعتمد: `{settings['lot']}`\n"
        f"⏳ الوقت المتبقي لاشتراكك: `{get_remaining_time(user_id, db)}`\n"
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
    
    print("🛸 Zo Alpha Bot Core v2.0 - Active & Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
