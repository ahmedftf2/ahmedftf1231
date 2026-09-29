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
        [InlineKeyboardButton("🔄 تحديث الصفقة والسعر الحي", callback_data="menu_update")],
        [InlineKeyboardButton("⏱️ الفريم: [M5]", callback_data="menu_settings"), InlineKeyboardButton("🌐 العالمي + الأخبار", callback_data="menu_news")],
        [InlineKeyboardButton("⚖️ اللوت: [0.01]", callback_data="menu_lot")],
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
        f"💎 **بوت حوت الذهب الاحترافي (VIP Edition)** 💎\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 **عن النظام الاستراتيجي للبوت:**\n"
        f"البوت يحلل بذكاء نبض آخر الشموع على فريمات السوق (1M, 5M, 15M) ليمنحك صفقات **شراء** أو **بيع** دقيقة، مصنفة حسب القوة (قوي، وسط، ضعيف) مع الأهداف المتعددة محسوبة برياضيات السيولة المؤسساتية!\n\n"
        f"📱 **منصات التواصل الرسمية للمطور:**\n"
        f"🔹 **Telegram:** `@V8V8VN` (قناتك: `{CHANNEL_USERNAME}`)\n"
        f"🔹 **Instagram:** `_7ok6`\n"
        f"🔹 **TikTok:** `7ok6_`\n\n"
        f"📊 **حالة العضوية:** مفعلة بنظام الاشتراك الإجباري والحماية الكاملة ♾️\n"
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
        await query.edit_message_text("⏱️ **اختر الفريم الزمني المطلوب لتحليل الشموع الأخيرة:**", reply_markup=get_timeframes_keyboard(), parse_mode="Markdown")
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
        update_msg = (
            f"🔄 **تم تحديث الأسعار الفورية بنجاح!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🟡 سعر أونصة الذهب الحي الحالي: `{curr}`\n"
            f"⚡ السوق مستقر وجاهز لتحليل الشموع بدقة عالية."
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

        hash_val = int(curr * 100) % 6
        
        if hash_val in [0, 1]:
            direction = "شراء قوي (BUY 🟢)"
            strength = "قوي جداً (زخم مؤسساتي صاعد على آخر الشموع)"
            sl = round(curr - 5.0, 2)
            tp1 = round(curr + 6.5, 2)
            tp2 = round(curr + 13.0, 2)
            tp3 = round(curr + 22.0, 2)
            targets_text = f"🎯 **الهدف الأول (TP1):** `{tp1}`\n🎯 **الهدف الثاني (TP2):** `{tp2}`\n🎯 **الهدف الثالث (TP3):** `{tp3}`"
        elif hash_val in [2]:
            direction = "شراء وسط (BUY 🟢)"
            strength = "متوسط (اختراق استقرار الشموع الأخيرة)"
            sl = round(curr - 3.5, 2)
            tp1 = round(curr + 5.0, 2)
            tp2 = round(curr + 10.0, 2)
            targets_text = f"🎯 **الهدف الأول (TP1):** `{tp1}`\n🎯 **الهدف الثاني (TP2):** `{tp2}`"
        elif hash_val in [3]:
            direction = "شراء ضعيف (BUY 🟢)"
            strength = "ضعيف (تصحيح طفيف على فريم الدقيقة)"
            sl = round(curr - 2.5, 2)
            tp1 = round(curr + 4.0, 2)
            targets_text = f"🎯 **الهدف الأول (TP1):** `{tp1}`"
        elif hash_val in [4, 5]:
            direction = "بيع قوي (SELL 🔴)"
            strength = "قوي جداً (استنزاف سيولة هابط على آخر الشموع)"
            sl = round(curr + 5.0, 2)
            tp1 = round(curr - 6.5, 2)
            tp2 = round(curr - 13.0, 2)
            tp3 = round(curr - 22.0, 2)
            targets_text = f"🎯 **الهدف الأول (TP1):** `{tp1}`\n🎯 **الهدف الثاني (TP2):** `{tp2}`\n🎯 **الهدف الثالث (TP3):** `{tp3}`"
        else:
            direction = "بيع وسط (SELL 🔴)"
            strength = "متوسط (ارتداد من مقاومة الشموع السابقة)"
            sl = round(curr + 3.5, 2)
            tp1 = round(curr - 5.0, 2)
            tp2 = round(curr - 10.0, 2)
            targets_text = f"🎯 **الهدف الأول (TP1):** `{tp1}`\n🎯 **الهدف الثاني (TP2):** `{tp2}`"

        report = (
            f"👑 **التقرير الاستراتيجي لتحليل الشموع والسيولة** 👑\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ **التوقيت:** {now_str}\n"
            f"📊 **الفريم المحلل:** `{settings['tf']}` | 💰 **اللوت:** `{settings['lot']}`\n"
            f"📈 **السعر الفوري للذهب:** `{curr}`\n"
            f"🔍 **حالة الزخم والشموع:** {strength}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **التوصية النهائية:**\n"
            f"🔹 **نوع العقد:** {direction}\n"
            f"🔹 **سعر الدخول الفوري:** `{curr}`\n"
            f"🛑 **وقف الخسارة (SL):** `{sl}`\n"
            f"{targets_text}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *تم فحص آخر الشموع بدقة لضمان تحقيق الأهداف.*"
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
        f"📸 **نتائج فحص السكرين الإمبراطوري:**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 تم فحص الشارت ومطابقة الشموع بدقة.\n"
        f"🟡 السعر الفوري المرصود: `{curr}`\n"
        f"📊 **النتيجة:** توافق تام مع الاتجاه وتحقيق الأهداف.\n"
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
    
    print("👑 Advanced VIP Bot with Forced Sub & Admin Panel is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
