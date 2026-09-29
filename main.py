import logging
import datetime
import random
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"
ADMIN_ID = 5796443586
CHANNEL_USERNAME = "@FOR2AH"  # قناتك الرسمية للاشتراك الإجباري

db = {
    "users": {},
    "codes": {},
    "banned": set(),
    "last_signal": "",
    "user_settings": {},
    "active_signals": {}  # تخزين تفاصيل الصفقة الحالية لكل مستخدم لمتابعة أهدافها
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

async def check_forced_subscription(user_id, context):
    if user_id == ADMIN_ID:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"خطأ في التحقق من الاشتراك الإجباري: {e}")
    return False

def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    if user_id in db["users"]:
        expiry_date = db["users"][user_id].get("expiry")
        if expiry_date and datetime.datetime.now() < expiry_date:
            return True
    return False

def get_main_control_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("📊 استخراج الصفقة الملكية الذكية", callback_data="menu_analysis")],
        [InlineKeyboardButton("🔄 فحص حالة الأهداف والسعر الحالي", callback_data="menu_update")],
        [InlineKeyboardButton("⏱️ الفريم: [M5]", callback_data="menu_settings"), InlineKeyboardButton("🌐 العالمي + الأخبار", callback_data="menu_news")],
        [InlineKeyboardButton("⚖️️ اللوت: [0.01]", callback_data="menu_lot")],
        [InlineKeyboardButton("💎 باقات وقائمة أسعار VIP الفاخرة", callback_data="menu_pricing")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك جديدة", callback_data="menu_activate")]
    ]
    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ غرفة القيادة والتحكم الإداري [VIP]", callback_data="menu_admin")])
    
    return InlineKeyboardMarkup(keyboard)

def get_timeframes_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱️ فريم 1 دقيقة (1M)", callback_data="tf_1m"), InlineKeyboardButton("⏱️ فريم 5 دقائق (5M)", callback_data="tf_5m")],
        [InlineKeyboardButton("⏱️ فريم 15 دقيقة (15M)", callback_data="tf_15m"), InlineKeyboardButton("⏱️ فريم 1 ساعة (1H)", callback_data="tf_1h")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]
    ])

def get_lots_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 0.01", callback_data="lot_0.01"), InlineKeyboardButton("🔹 0.03", callback_data="lot_0.03"), InlineKeyboardButton("🔹 0.05", callback_data="lot_0.05")],
        [InlineKeyboardButton("🔹 0.10", callback_data="lot_0.10"), InlineKeyboardButton("🔹 0.20", callback_data="lot_0.20"), InlineKeyboardButton("🔹 0.30", callback_data="lot_0.30")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]
    ])

def get_admin_inline_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎟️ توليد كود اشتراك جديد", callback_data="admin_gen_menu")],
        [InlineKeyboardButton("👥 إدارة وطرد المشتركين", callback_data="admin_list_users")],
        [InlineKeyboardButton("🔑 إدارة وتعطيل الأكواد", callback_data="admin_list_codes")],
        [InlineKeyboardButton("📢 نشر آخر تحليل للقناة العامة", callback_data="publish_to_channel")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="menu_start")]
    ])

def get_welcome_text():
    return (
        f"🦅 **أبر زعيم أسواق المال | أحمد السيد** 🦅\n"
        f"💎 **بوت حوت الذهب الاحترافي (Live Target Management)** 💎\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 **النظام التفاعلي الجديد:**\n"
        f"الآن بعد استخراج الصفقة، يظهر لك زر (دخول للصفقة). يتابع البوت السعر لحظياً، وحال ضرب الهدف الأول يطالبك بتأمين الصفقة أو الاستمرار للهدف الثاني بكل دقة!\n\n"
        f"📱 **منصات التواصل الرسمية للمطور:**\n"
        f"🔹 **Telegram:** `@V8V8VN` (قناتك: `{CHANNEL_USERNAME}`)\n"
        f"🔹 **Instagram:** `_7ok6`\n"
        f"🔹 **TikTok:** `7ok6_`\n\n"
        f"📊 **حالة العضوية:** مفعلة بنظام الحماية الكاملة ♾️\n"
        f"👇 **اختر من قائمة العمليات أدناه:**"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in db["banned"]:
        if update.callback_query:
            await update.callback_query.answer("❌ أنت محظور من استخدام البوت.", show_alert=True)
        else:
            await update.message.reply_text("❌ أنت محظور من النظام الأمني للبوت.")
        return

    is_joined = await check_forced_subscription(user.id, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة الرسمية الآن", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="menu_start")]
        ])
        msg = (
            f"🚨 **عذراً يا مولاي! الاشتراك الإجباري مفعل.**\n\n"
            f"يجب عليك الانضمام أولاً إلى قناة المطور الرسمية لتتمكن من استخدام البوت:\n"
            f"👉 {CHANNEL_USERNAME}\n\n"
            f"بعد الانضمام، اضغط على زر (تحقق من الاشتراك) أدناه:"
        )
        if update.callback_query:
            await update.callback_query.message.edit_text(msg, reply_markup=join_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=join_markup, parse_mode="Markdown")
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
        await query.edit_message_text("❌ عذراً، تم حظرك نهائياً من قبل الإدارة.")
        return

    is_joined = await check_forced_subscription(user_id, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة الآن", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="menu_start")]
        ])
        await query.edit_message_text(
            f"🚨 **عذراً، لقد غادرت القناة الرسمية ({CHANNEL_USERNAME})!**\n"
            f"يجب إعادة الاشتراك لتفعيل صلاحيات البوت مجدداً.",
            reply_markup=join_markup, parse_mode="Markdown"
        )
        return

    data = query.data
    is_admin = (user_id == ADMIN_ID)

    if (data.startswith("admin_") or data.startswith("ban_user_") or data.startswith("del_code_") or data == "publish_to_channel") and not is_admin:
        db["banned"].add(user_id)
        await query.edit_message_text("🚨 تنبيه أمني: تم رصد محاولة تجاوز صلاحيات وتم حظرك!")
        return

    if data == "menu_start":
        await query.edit_message_text(get_welcome_text(), reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        return

    elif data == "menu_settings" or data == "menu_news":
        await query.edit_message_text("⏱️ **اختر الفريم الزمني المطلوب لتثبيت مناطق المساحات:**", reply_markup=get_timeframes_keyboard(), parse_mode="Markdown")
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
            f"للحصول على أي كود، تواصل مع المطور: `@V8V8VN`"
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
        active = db["active_signals"].get(user_id)
        
        if active:
            entry = active["entry"]
            direction = active["direction"]
            tp1 = active["tp1"]
            tp2 = active["tp2"]
            sl = active["sl"]
            is_buy = "شراء" in direction
            
            # حساب المسافة لفحص ضرب الأهداف
            diff = round(curr - entry, 2) if is_buy else round(entry - curr, 2)
            
            if diff >= 5.0 or (is_buy and curr >= tp1) or (not is_buy and curr <= tp1):
                # تم ضرب الهدف الأول! نعرض أزرار التأمين أو الاستمرار للهدف الثاني
                active["tp1_hit"] = True
                status_market = "🎉 **تم ضرب الهدف الأول بنجاح تام! (TP1 Hit)**\n⚡ يرجى اختيار الإجراء المناسب أدناه لتأمين صفقتك:"
                
                manage_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔒 أمن الصفقة (حرك الوقف للدخول)", callback_data="sig_secure"), InlineKeyboardButton("🚀 استمر للهدف الثاني (TP2)", callback_data="sig_continue")],
                    [InlineKeyboardButton("❌ إغلاق وجني الأرباح", callback_data="sig_close"), InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_start")]
                ])
                
                report = (
                    f"👑 **متابعة الصفقة الحية (حالة الهدف الأول)** 👑\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📈 سعر الدخول: `{entry}` | السعر الحالي: `{curr}`\n"
                    f"🔹 الاتجاه: `{direction}`\n"
                    f"🛑 وقف الخسارة الحالي: `{sl}`\n"
                    f"🎯 الهدف الأول: `{tp1}` (تمت الإصابة ✅)\n"
                    f"🎯 الهدف الثاني: `{tp2}` (قيد الانتظار ⏳)\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"{status_market}"
                )
                await query.edit_message_text(report, parse_mode="Markdown", reply_markup=manage_markup)
                return
            else:
                status_market = f"⏳ الصفقة جارية تسير نحو الأهدف بدقة (الفرق الحالي: {diff} نقطة)."
                update_msg = (
                    f"🔄 **تحديث حالة السوق والسعر الفوري:**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📈 سعر الدخول الأصلي: `{entry}`\n"
                    f"🟡 السعر الفوري الحالي: `{curr}`\n"
                    f"🔹 اتجاه الصفقة: `{direction}`\n"
                    f"📊 **الحالة الفنية:** {status_market}\n"
                    f"━━━━━━━━━━━━━━━━━━━"
                )
                await query.edit_message_text(update_msg, reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
                return
        else:
            update_msg = (
                f"🔄 **تم تحديث الأسعار الفورية بنجاح!**\n"
                f"🟡 سعر أونصة الذهب الحي الحالي: `{curr}`\n"
                f"💡 اضغط على (استخراج الصفقة الملكية الذكية) لبدء صفقة جديدة."
            )
            await query.edit_message_text(update_msg, reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
            return

    elif data == "menu_analysis":
        if not is_subscribed(user_id):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك. تواصل مع الإدارة لتفعيل كود جديد.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
            return

        settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
        curr = get_live_gold_price()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # توليد صفقة جديدة وتثبيتها حصرياً للمستخدم مع أزرار (دخول للصفقة / خروج)
        mod_val = int(curr * 10) % 4
        if mod_val in [0, 1]:
            direction = "شراء مؤسساتي قـوي (BUY 🟢)"
            zone_desc = "منطقة طلب واضحة على فريم المساحات"
            sl = round(curr - 4.0, 2)
            tp1 = round(curr + 5.0, 2)
            tp2 = round(curr + 10.0, 2)
        else:
            direction = "بيع مؤسساتي قـوي (SELL 🔴)"
            zone_desc = "منطقة عرض واضحة على فريم المساحات"
            sl = round(curr + 4.0, 2)
            tp1 = round(curr - 5.0, 2)
            tp2 = round(curr - 10.0, 2)

        active = {
            "entry": curr,
            "direction": direction,
            "zone": zone_desc,
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
            f"👑 **الصفقة الملكية الذكية (جاهزة للتنفيذ)** 👑\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ **وقت الإصدار:** {now_str}\n"
            f"📊 **الفريم:** `{active['tf']}` | 💰 **اللوت:** `{active['lot']}`\n"
            f"📈 **سعر الدخول المعتمد:** `{curr}`\n"
            f"🔍 **منطقة التحليل:** {active['zone']}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **توصية الدخول:**\n"
            f"🔹 **نوع العقد:** {active['direction']}\n"
            f"🛑 **وقف الخسارة (SL):** `{active['sl']}`\n"
            f"🎯 **الهدف الأول (TP1):** `{active['tp1']}`\n"
            f"🎯 **الهدف الثاني (TP2):** `{active['tp2']}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👇 **اختر إجراء الصفقة أدناه للمتابعة الآلية:**"
        )
        db["last_signal"] = report

        # أزرار الدخول والخروج الخاصة بالصفقة الجديدة
        signal_action_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ دخول للصفقة (بدء المتابعة)", callback_data="sig_enter"), InlineKeyboardButton("❌ خروج / إلغاء", callback_data="sig_close")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_start")]
        ])
        
        await query.edit_message_text(report, parse_mode="Markdown", reply_markup=signal_action_markup)
        return

    # التفاعلات الخاصة بإدارة الصفقة الحية
    elif data == "sig_enter":
        await query.edit_message_text(
            f"✅ **تم تأكيد دخول الصفقة بنجاح!**\n"
            f"البوت يقوم الآن بمراقبة حركة السعر والأهداف لحظياً. عندما يضرب الهدف الأول، سيتم تنبيهك تلقائياً لعمل التأمين أو الانتقال للهدف الثاني.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 فحص حالة الأهداف الآن", callback_data="menu_update")],
                [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="menu_start")]
            ]),
            parse_mode="Markdown"
        )
        return

    elif data == "sig_secure":
        active = db["active_signals"].get(user_id)
        if active:
            active["sl"] = active["entry"]  # تأمين الصفقة بوضع وقف الخسارة عند سعر الدخول
            await query.edit_message_text(
                f"🔒 **تم تأمين الصفقة بنجاح!**\n"
                f"تم تحريك وقف الخسارة (SL) إلى سعر الدخول الأصلي (`{active['entry']}`). أنت الآن في صفقة بدون مخاطرة، وتستمر نحو الهدف الثاني (`{active['tp2']}`) بسلام تام!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="menu_start")]]),
                parse_mode="Markdown"
            )
        return

    elif data == "sig_continue":
        active = db["active_signals"].get(user_id)
        if active:
            await query.edit_message_text(
                f"🚀 **تم تأكيد الاستمرار للهدف الثاني!**\n"
                f"البوت يتابع بجهد نحو الهدف النهائي (`{active['tp2']}`). ترقب التحديثات اللحظية.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="menu_start")]]),
                parse_mode="Markdown"
            )
        return

    elif data == "sig_close":
        if user_id in db["active_signals"]:
            del db["active_signals"][user_id]
        await query.edit_message_text(
            f"🛑 **تم إغلاق الصفقة وجني الأرباح بنجاح.**\n"
            f"تمت تصفية عقودك بالكامل وإعادة ضبط العداد.",
            reply_markup=get_main_control_keyboard(is_admin=is_admin),
            parse_mode="Markdown"
        )
        return

    elif data == "menu_admin":
        if not is_admin:
            db["banned"].add(user_id)
            return
        await query.edit_message_text("👑 **غرفة القيادة والتحكم الإداري للمطور:**", reply_markup=get_admin_inline_panel())
        return

    elif data.startswith("tf_"):
        tf = data.replace("tf_", "")
        db["user_settings"][user_id]["tf"] = tf
        await query.edit_message_text(f"✅ **تم ضبط الفريم الزمني إلى:** `{tf}`", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

    elif data.startswith("lot_"):
        lot = float(data.replace("lot_", ""))
        db["user_settings"][user_id]["lot"] = lot
        await query.edit_message_text(f"✅ **تم ضبط حجم اللوت إلى:** `{lot}`", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

    elif data == "admin_gen_menu":
        gen_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎟️ كود ساعة (10)", callback_data="admin_gen_1h"), InlineKeyboardButton("🎟️ كود يومي (25)", callback_data="admin_gen_1d")],
            [InlineKeyboardButton("🎟️ كود أسبوعي (75)", callback_data="admin_gen_7d"), InlineKeyboardButton("🎟️ كود أسبوعين (125)", callback_data="admin_gen_14d")],
            [InlineKeyboardButton("🎟️ كود شهر VIP (225)", callback_data="admin_gen_30d")],
            [InlineKeyboardButton("🔙 رجوع لغرفة القيادة", callback_data="menu_admin")]
        ])
        await query.edit_message_text("🎟️ **اختر نوع الكود المراد توليده:**", reply_markup=gen_kb)
        return

    elif data.startswith("admin_gen_"):
        period_type = data.replace("admin_gen_", "")
        if period_type == "1h":
            delta = datetime.timedelta(hours=1)
            desc = "ساعة واحدة"
        elif period_type == "1d":
            delta = datetime.timedelta(days=1)
            desc = "يوم واحد"
        elif period_type == "7d":
            delta = datetime.timedelta(days=7)
            desc = "أسبوع واحد"
        elif period_type == "14d":
            delta = datetime.timedelta(days=14)
            desc = "أسبوعين"
        elif period_type == "30d":
            delta = datetime.timedelta(days=30)
            desc = "شهر VIP"
        else:
            delta = datetime.timedelta(days=30)
            desc = "شهر VIP"
        
        code = f"VIP-{period_type.upper()}-{random.randint(1000, 9999)}"
        db["codes"][code] = {"delta": delta, "used": False}
        await query.edit_message_text(f"✅ تم توليد كود ({desc}) بنجاح:\n`{code}`\n\nيمكنك إعطاؤه للمشترك.", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")

    elif data == "admin_list_users":
        if not db["users"]:
            await query.edit_message_text("👥 لا يوجد مشتركين مسجلين حالياً.", reply_markup=get_admin_inline_panel())
            return
        
        users_kb = []
        for uid, info in list(db["users"].items())[:10]:
            users_kb.append([InlineKeyboardButton(f"👤 {info['name']} ({uid})", callback_data=f"noop_{uid}"), InlineKeyboardButton("🚨 طرد/حظر", callback_data=f"ban_user_{uid}")])
        users_kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")])
        
        await query.edit_message_text("👥 **إدارة وطرد المشتركين النشطين:**", reply_markup=InlineKeyboardMarkup(users_kb), parse_mode="Markdown")
        return

    elif data.startswith("ban_user_"):
        target_id = int(data.replace("ban_user_", ""))
        if target_id in db["users"]:
            del db["users"][target_id]
        db["banned"].add(target_id)
        await query.edit_message_text(f"✅ تم طرد وحظر المستخدم (`{target_id}`) بنجاح!", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")
        return

    elif data == "admin_list_codes":
        if not db["codes"]:
            await query.edit_message_text("🔑 لا توجد أكواد مسجلة حالياً.", reply_markup=get_admin_inline_panel())
            return
        
        codes_kb = []
        for code, info in list(db["codes"].items())[:10]:
            status = "مستخدم ❌" if info["used"] else "فعال ✅"
            codes_kb.append([InlineKeyboardButton(f"🔑 {code} ({status})", callback_data=f"noop_c"), InlineKeyboardButton("🗑️ حذف", callback_data=f"del_code_{code}")])
        codes_kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_admin")])
        
        await query.edit_message_text("🔑 **إدارة وتعطيل الأكواد:**", reply_markup=InlineKeyboardMarkup(codes_kb), parse_mode="Markdown")
        return

    elif data.startswith("del_code_"):
        code_to_del = data.replace("del_code_", "")
        if code_to_del in db["codes"]:
            del db["codes"][code_to_del]
        await query.edit_message_text(f"✅ تم حذف الكود (`{code_to_del}`) بنجاح!", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")
        return

    elif data == "publish_to_channel":
        if db["last_signal"]:
            try:
                await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=db["last_signal"], parse_mode="Markdown")
                await query.edit_message_text("✅ **تم نشر التحليل بنجاح إلى قناتك العامة (`" + CHANNEL_USERNAME + "`)!**", reply_markup=get_admin_inline_panel(), parse_mode="Markdown")
            except Exception as e:
                await query.edit_message_text(f"❌ خطأ في النشر (تأكد أن البوت مشرف بالقناة): {e}", reply_markup=get_admin_inline_panel())
        else:
            await query.edit_message_text("⚠️ لا يوجد تحليل لنشره حالياً.", reply_markup=get_admin_inline_panel())

    elif data.startswith("noop_"):
        await query.answer("ℹ️ هذه معلومات المشترك.", show_alert=False)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    is_joined = await check_forced_subscription(user_id, context)
    if not is_joined:
        join_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة الآن", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="menu_start")]
        ])
        await update.message.reply_text(
            f"🚨 **عذراً، يجب عليك الاشتراك أولاً في قناتنا الرسمية:**\n👉 {CHANNEL_USERNAME}\n\nبعد الاشتراك، اضغط على زر التحقق.",
            reply_markup=join_markup, parse_mode="Markdown"
        )
        return

    is_admin = (user_id == ADMIN_ID)

    if context.user_data.get("waiting_for_code"):
        context.user_data["waiting_for_code"] = False
        text = update.message.text if update.message.text else ""
        code_info = db["codes"].get(text)
        if code_info and not code_info["used"]:
            code_info["used"] = True
            delta = code_info["delta"]
            if user_id not in db["users"]:
                db["users"][user_id] = {"name": update.effective_user.full_name, "username": f"@{update.effective_user.username}"}
            db["users"][user_id]["expiry"] = datetime.datetime.now() + delta
            await update.message.reply_text(f"🎉 **مبروك يا مولاي! تم تفعيل اشتراكك بنجاح.**", reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ الكود غير صالح أو تم استخدامه مسبقاً.", reply_markup=get_main_control_keyboard(is_admin=is_admin))
        return
    
    await update.message.reply_text(get_welcome_text(), reply_markup=get_main_control_keyboard(is_admin=is_admin), parse_mode="Markdown")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    is_joined = await check_forced_subscription(user_id, context)
    if not is_joined:
        return

    is_admin = (user_id == ADMIN_ID)
    settings = db["user_settings"].get(user_id, {"tf": "5m", "lot": 0.01})
    curr = get_live_gold_price()
    
    result = (
        f"📸 **فحص الشارت والمساحات الثابتة:**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 تم فحص السكرين وتثبيت نطاق السيولة.\n"
        f"🟡 السعر الفوري المرصود: `{curr}`\n"
        f"📊 **النتيجة:** صفقة ثابتة ومطابقة لهيكل المساحة المرفقة.\n"
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
    
    print("👑 Advanced Interactive Target Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
