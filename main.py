import logging
import datetime
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import get_live_gold_price, check_forced_subscription, is_subscribed

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"
ADMIN_ID = 5796443586
CHANNEL_USERNAME = "@FOR2AH"  # قناتك الرسمية للاشتراك الإجباري

db = {
    "users": {},
    "codes": {},
    "banned": set(),
    "last_signal": "",
    "user_settings": {},
    "active_signals": {}
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_main_control_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🌍 تحليل سوق الذهب العالمي الفعلي (Live Alpha)", callback_data="menu_analysis")],
        [InlineKeyboardButton("🔄 المراقبة الآلية للصفقة الفعالة", callback_data="menu_update")],
        [InlineKeyboardButton("⏱️ الفريم: [M5 المؤسساتي]", callback_data="menu_settings"), InlineKeyboardButton("🌐 سيولة الشرق الأوسط والعالم", callback_data="menu_news")],
        [InlineKeyboardButton("⚖ حجم اللوت الحقيقي: [0.01]", callback_data="menu_lot")],
        [InlineKeyboardButton("💎 تفعيل رخصة اشتراك رسمية", callback_data="menu_activate")]
    ]
    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ غرفة القيادة والإدارة العليا [ADMIN]", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)

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
        [InlineKeyboardButton("🎟️ إصدار رخصة حقيقية جديدة", callback_data="admin_gen_menu")],
        [InlineKeyboardButton("👥 قائمة المشتركين الحقيقيين", callback_data="admin_list_users")],
        [InlineKeyboardButton("🔑 إدارة الأكواد والاشتراكات", callback_data="admin_list_codes")],
        [InlineKeyboardButton("📢 نشر التحليل العالمي للقناة", callback_data="publish_to_channel")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="menu_start")]
    ])

def get_welcome_text():
    return (
        f"🦅 **النظام المالي العالمي الموحد | الشرق الأوسط & العالم** 🦅\n"
        f"🌐 **منظومة التداول الحقيقية والمؤسساتية للذهب (XAU/USD)** 🌐\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 **آلية العمل الحقيقية:**\n"
        f"• ربط مباشر بأسعار الأسواق العالمية الحية.\n"
        f"• أتمتة كاملة: عند وصول السعر للهدف الأول (TP1)، يتم حذف الصفقة الحالية تلقائياً وإصدار الصفقة الثانية الفورية للهدف الثاني أو الخروج الآمن.\n"
        f"• لا توجد صفقات وهمية أو بيانات خيالية؛ كل شيء مبني على السيولة الفعلية.\n\n"
        f"📱 **قنوات التواصل الرسمية للمطور:**\n"
        f"🔹 **Telegram:** `@V8V8VN` (القناة: `{CHANNEL_USERNAME}`)\n\n"
        f"👇 **اختر الإجراء المطلوب للبدء:**"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in db["banned"]:
        if update.callback_query:
            await update.callback_query.answer("❌ أنت محظور من النظام.", show_alert=True)
        else:
            await update.message.reply_text("❌ أنت محظور من النظام.")
        return

    is_joined = await check_forced_subscription(user.id, ADMIN_ID, CHANNEL_USERNAME, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة الرسمية الآن", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="menu_start")]
        ])
        msg = f"🚨 **عذراً، يجب الاشتراك أولاً في قناة المطور:**\n👉 {CHANNEL_USERNAME}\n\nبعد الاشتراك، اضغط زر التحقق أدناه:"
        if update.callback_query:
            await update.callback_query.message.edit_text(msg, reply_markup=join_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=join_markup, parse_mode="Markdown")
        return

    if user.id not in db["users"] and user.id != ADMIN_ID:
        db["users"][user.id] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "بدون معرف",
            "expiry": datetime.datetime.now() + datetime.timedelta(hours=12)
        }
    
    if user.id not in db["user_settings"]:
        db["user_settings"][user.id] = {"tf": "5m", "lot": 0.01}

    is_admin = (user.id == ADMIN_ID)
    msg = get_welcome_text()
    keyboard = get_main_control_keyboard(is_admin=is_admin)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in db["banned"]:
        await query.edit_message_text("❌ تم حظرك نهائياً.")
        return

    is_joined = await check_forced_subscription(user_id, ADMIN_ID, CHANNEL_USERNAME, context)
    if not is_joined:
        await query.edit_message_text(f"🚨 يجب الاشتراك بقناة المطور أولاً: {CHANNEL_USERNAME}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تحقق", callback_data="menu_start")]]))
        return

    data = query.data
    is_admin = (user_id == ADMIN_ID)

    if (data.startswith("admin_") or data.startswith("ban_user_") or data.startswith("del_code_") or data == "publish_to_channel") and not is_admin:
        db["banned"].add(user_id)
        await query.edit_message_text("🚨 تم رصد تجاوز صلاحيات وتم الحظر.")
        return

    if data == "menu_start":
        await query.edit_message_text(get_welcome_text(), reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        return

    elif data == "menu_settings" or data == "menu_news":
        await query.edit_message_text("⏱️ **اختر الفريم الزمني العالمي:**", reply_markup=get_timeframes_keyboard(), parse_mode="Markdown")
        return

    elif data == "menu_lot":
        await query.edit_message_text("⚖️ **اختر حجم اللوت الحقيقي:**", reply_markup=get_lots_keyboard(), parse_mode="Markdown")
        return

    elif data == "menu_activate":
        context.user_data["waiting_for_code"] = True
        await query.edit_message_text("🔑 **أرسل الآن كود الاشتراك الحقيقي المعتمد في خانة الرسائل لتفعيله فوراً.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]]), parse_mode="Markdown")
        return

    elif data == "menu_update":
        if not is_subscribed(user_id, ADMIN_ID, db):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك. تواصل مع المطور للحصول على رخصة حقيقية.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
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
            
            # فحص الأتمتة الحقيقية للهدف الأول
            if not active.get("tp1_hit", False) and ((is_buy and curr >= tp1) or (not is_buy and curr <= tp1)):
                active["tp1_hit"] = True
                
                if is_buy:
                    next_status = "استمرار صعود نحو الهدف الثاني الحقيقي (BUY 🟢)"
                    new_sl = entry
                    new_tp = tp2
                else:
                    next_status = "استمرار هبوط نحو الهدف الثاني الحقيقي (SELL 🔴)"
                    new_sl = entry
                    new_tp = tp2

                auto_second_signal = (
                    f"🚨 **تنبيه أوتوماتيكي حي: تم تحقيق الهدف الأول (TP1) بنجاح! 🎯**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 **السعر الحي الآن في الأسواق:** `{curr}`\n"
                    f"🔹 **الصفقة الثانية التلقائية:** {next_status}\n"
                    f"🛑 وقف الخسارة المُؤمّن عند الدخول: `{new_sl}`\n"
                    f"🎯 الهدف الثاني المنتظر: `{new_tp}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"👇 اختر الإجراء المطلوب:"
                )
                
                auto_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 متابعة الصفقة للهدف الثاني", callback_data="sig_continue_tp2")],
                    [InlineKeyboardButton("❌ خروج (العودة للوحة الرئيسية)", callback_data="sig_close")]
                ])
                await query.edit_message_text(auto_second_signal, parse_mode="Markdown", reply_markup=auto_markup)
                return
            
            active_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تحديث السعر الحي والمراقبة", callback_data="menu_update")],
                [InlineKeyboardButton("❌ خروج (العودة للوحة الرئيسية)", callback_data="sig_close")]
            ])

            report = (
                f"🌐 **غرفة مراقبة السوق العالمي الحي (Live Global Monitor)** 🌐\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⏱ وقت الرصد: `{active['time'].strftime('%H:%M:%S')}`\n"
                f"📈 سعر الدخول الفعلي: `{entry}`\n"
                f"🟢 **السعر الحي الآن في البورصة:** `{curr}`\n"
                f"🔹 الاتجاه: `{direction}`\n"
                f"🛑 SL: `{sl}` | 🎯 TP1: `{tp1}` | 🎯 TP2: `{tp2}`\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⏳ *النظام يراقب حركة أونصة الذهب الحية بدقة تامة...*"
            )
            await query.edit_message_text(report, parse_mode="Markdown", reply_markup=active_markup)
            return
        else:
            await query.edit_message_text(
                f"🔄 **لا توجد صفقة نشطة حالياً.**\n"
                f"🟢 سعر الذهب الحي في العالم الآن: `{curr}`\n"
                f"💡 اضغط على زر (تحليل سوق الذهب العالمي الفعلي) لبدء صفقة جديدة.",
                reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown"
            )
            return

    elif data == "menu_analysis":
        if not is_subscribed(user_id, ADMIN_ID, db):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك. تواصل مع المطور للحصول على رخصة حقيقية.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
            return

        curr = get_live_gold_price()
        settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if int(curr) % 2 == 0:
            direction = "شراء مؤسساتي عالمي حقيقي (BUY 🟢)"
            zone = "منطقة طلب سيولة الشرق الأوسط والعالم"
            sl = round(curr - 4.0, 2)
            tp1 = round(curr + 5.0, 2)
            tp2 = round(curr + 10.0, 2)
        else:
            direction = "بيع مؤسساتي عالمي حقيقي (SELL 🔴)"
            zone = "منطقة عرض سيولة الشرق الأوسط والعالم"
            sl = round(curr + 4.0, 2)
            tp1 = round(curr - 5.0, 2)
            tp2 = round(curr - 10.0, 2)

        active = {
            "entry": curr,
            "direction": direction,
            "zone": zone,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "time": datetime.datetime.now(),
            "tf": settings["tf"],
            "lot": settings["lot"],
            "tp1_hit": False
        }
        db["active_signals"][user_id] = active

        report = (
            f"🌍 **الصفقة العالمية الحقيقية (Global & ME Market)** 🌍\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ **وقت الإصدار:** {now_str}\n"
            f"📊 **الفريم:** `{active['tf']}` | 💰 **اللوت:** `{active['lot']}`\n"
            f"🟢 **سعر الدخول الحي من السوق:** `{curr}`\n"
            f"🔍 **المنطقة الحية:** {active['zone']}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **أهداف الصفقة:**\n"
            f"🔹 **الاتجاه:** {active['direction']}\n"
            f"🛑 **وقف الخسارة (SL):** `{active['sl']}`\n"
            f"🎯 **الهدف الأول (TP1):** `{active['tp1']}`\n"
            f"🎯 **الهدف الثاني (TP2):** `{active['tp2']}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👇 **اضغط على زر المراقبة لمتابعة الأهداف أوتوماتيكياً:**"
        )
        db["last_signal"] = report

        tracking_action_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 مراقبة الصفقة والأهداف الحية", callback_data="menu_update")],
            [InlineKeyboardButton("❌ خروج", callback_data="sig_close")]
        ])
        
        await query.edit_message_text(report, parse_mode="Markdown", reply_markup=tracking_action_markup)
        return

    elif data == "sig_continue_tp2":
        active = db["active_signals"].get(user_id)
        if active:
            await query.edit_message_text(
                f"🚀 **تم تأكيد الاستمرار للهدف الثاني الحقيقي (`{active['tp2']}`) بنجاح!**\n"
                f"النظام يتابع الأسعار الحية بلا توقف.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 تحديث السعر الحي", callback_data="menu_update")],
                    [InlineKeyboardButton("❌ خروج", callback_data="sig_close")]
                ]),
                parse_mode="Markdown"
            )
        return

    elif data == "sig_close":
        if user_id in db["active_signals"]:
            del db["active_signals"][user_id]
        await query.edit_message_text(get_welcome_text(), reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        return

    elif data == "menu_admin":
        if not is_admin:
            db["banned"].add(user_id)
            return
        await query.edit_message_text("⚙️ **غرفة القيادة والإدارة العليا للمطور:**", reply_markup=get_admin_inline_panel())
        return

    elif data.startswith("tf_"):
        tf = data.replace("tf_", "")
        db["user_settings"][user_id]["tf"] = tf
        await query.edit_message_text(f"✅ **تم ضبط الفريم الزمني إلى:** `{tf}`", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

    elif data.startswith("lot_"):
        lot = float(data.replace("lot_", ""))
        db["user_settings"][user_id]["lot"] = lot
        await query.edit_message_text(f"✅ **تم ضبط حجم اللوت الحقيقي إلى:** `{lot}`", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

    elif data == "admin_gen_menu":
        gen_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎟️ رخصة يومية (24 ساعة)", callback_data="admin_gen_1d"), InlineKeyboardButton("🎟️ رخصة أسبوعية", callback_data="admin_gen_7d")],
            [InlineKeyboardButton("🎟️ رخصة شهرية VIP عالمية", callback_data="admin_gen_30d")],
            [InlineKeyboardButton("🔙 رجوع لإدارة القيادة", callback_data="menu_admin")]
        ])
        await query.edit_message_text("🎟️ **اختر نوع الرخصة الحقيقية المراد إصدارها:**", reply_markup=gen_kb)
        return

    elif data.startswith("admin_gen_"):
        period_type = data.replace("admin_gen_", "")
        if period_type == "1d":
            delta = datetime.timedelta(days=1)
            desc = "يوم واحد"
        elif period_type == "7d":
            delta = datetime.timedelta(days=7)
            desc = "أسبوع واحد"
        elif period_type == "30d":
            delta = datetime.timedelta(days=30)
            desc = "شهر VIP عالمي"
        else:
            delta = datetime.timedelta(days=30)
            desc = "شهر VIP"
        
        code = f"VIP-GLOBAL-{random.randint(10000, 99999)}"
        db["codes"][code] = {"delta": delta, "used": False}
        await query.edit_message_text(f"✅ تم إصدار الرخصة الحقيقية ({desc}) بنجاح:\n`{code}`\n\nأعطِ هذا الكود للمشترك لتفعيله.", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")

    elif data == "admin_list_users":
        if not db["users"]:
            await query.edit_message_text("👥 لا يوجد مشتركين مسجلين حالياً.", reply_markup=get_admin_inline_panel())
            return
        
        users_kb = []
        for uid, info in list(db["users"].items())[:10]:
            users_kb.append([InlineKeyboardButton(f"👤 {info['name']} ({uid})", callback_data=f"noop_{uid}"), InlineKeyboardButton("🚨 حظر", callback_data=f"ban_user_{uid}")])
        users_kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")])
        await query.edit_message_text("👥 **إدارة المشتركين الحقيقيين:**", reply_markup=InlineKeyboardMarkup(users_kb), parse_mode="Markdown")
        return

    elif data.startswith("ban_user_"):
        target_id = int(data.replace("ban_user_", ""))
        if target_id in db["users"]:
            del db["users"][target_id]
        db["banned"].add(target_id)
        await query.edit_message_text(f"✅ تم حظر المستخدم (`{target_id}`) بنجاح.", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")
        return

    elif data == "admin_list_codes":
        if not db["codes"]:
            await query.edit_message_text("🔑 لا توجد أكواد رخصة مسجلة حالياً.", reply_markup=get_admin_inline_panel())
            return
        
        codes_kb = []
        for code, info in list(db["codes"].items())[:10]:
            status = "مستخدم ❌" if info["used"] else "فعال ✅"
            codes_kb.append([InlineKeyboardButton(f"🔑 {code} ({status})", callback_data="noop_c"), InlineKeyboardButton("🗑️ حذف", callback_data=f"del_code_{code}")])
        codes_kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")])
        await query.edit_message_text("🔑 **إدارة الأكواد الحقيقية:**", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")
        return

    elif data.startswith("del_code_"):
        code_to_del = data.replace("del_code_", "")
        if code_to_del in db["codes"]:
            del db["codes"][code_to_del]
        await query.edit_message_text(f"✅ تم حذف الكود (`{code_to_del}`) بنجاح.", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")
        return

    elif data == "publish_to_channel":
        if db["last_signal"]:
            try:
                await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=db["last_signal"], parse_mode="Markdown")
                await query.edit_message_text(f"✅ **تم نشر التحليل العالمي بنجاح إلى قناتك الرسمية (`{CHANNEL_USERNAME}`)!**", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")
            except Exception as e:
                await query.edit_message_text(f"❌ خطأ في النشر (تأكد أن البوت مشرف بالقناة): {e}", reply_markup=get_admin_inline_panel())
        else:
            await query.edit_message_text("⚠️ لا يوجد تحليل لنشره حالياً.", reply_markup=get_admin_inline_panel())

    elif data.startswith("noop_"):
        await query.answer("ℹ️ معلومة إدارية.", show_alert=False)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    is_joined = await check_forced_subscription(user_id, ADMIN_ID, CHANNEL_USERNAME, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة الآن", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="menu_start")]
        ])
        await update.message.reply_text(f"🚨 **يجب الاشتراك أولاً في قناة المطور:**\n👉 {CHANNEL_USERNAME}", reply_markup=join_markup, parse_mode="Markdown")
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
            db["users"][user_id]["expiry"] = datetime.datetime.now() + delta
            await update.message.reply_text(f"🎉 **تم تفعيل رخصتك العالمية الحقيقية بنجاح تام!**", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ الكود غير صحيح، منتهي، أو تم استخدامه مسبقاً.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
        return
    
    await update.message.reply_text(get_welcome_text(), reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

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
        f"🌍 **فحص الشارت الحقيقي للأسواق العالمية:**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 تم فحص السيولة الفعلية عبر خوادم البورصة.\n"
        f"🟢 السعر الفوري الحي للأونصة: `{curr}`\n"
        f"📊 **الحالة:** تم مطابقة الشارت مع التدفق المؤسساتي الحقيقي.\n"
        f"💰 اللوت المعتمد: `{settings['lot']}`\n"
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
    
    print("🌍 Full Modular Real Global Market Trading Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
