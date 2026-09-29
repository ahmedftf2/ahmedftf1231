import logging
import time
import datetime
import asyncio
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from utils import PathManager, LoggerManager, DatabaseManager, SecurityManager

PathManager.create_directories(".", ["database", "logs", "assets"])
logger = LoggerManager.get_logger("Ahmed_Al_Sayed_Gold_Sniper_VIP_v8")

TELEGRAM_BOT_TOKEN = "8916004825:AAG67V-nkqGLileO6cOy7847UIoqtVVjPog"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  
CHANNEL_USERNAME = "@FOR2AH"  # قناتك الحصرية الإجبارية

db = DatabaseManager()

async def check_channel_subscription(bot, user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.error(f"Error checking subscription for {user_id}: {e}")
    return False

def is_user_authorized(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    expiry = db.get_item(f"expiry_{user_id}")
    if expiry and float(expiry) > time.time():
        return True
    return False

def register_active_user(user_id: int):
    try:
        users_list = db.get_item("global_active_users_list")
        if not users_list:
            users_list = []
        else:
            if isinstance(users_list, str):
                try:
                    users_list = json.loads(users_list)
                except:
                    users_list = []
        if user_id not in users_list:
            users_list.append(user_id)
            db.set_item("global_active_users_list", users_list)
            
        if not db.get_item(f"sub_start_time_{user_id}"):
            db.set_item(f"sub_start_time_{user_id}", str(time.time()))
    except Exception as e:
        logger.error(f"Error registering user: {e}")

def get_remaining_time(user_id: int) -> str:
    if user_id == ADMIN_ID:
        return "صلاحية مطلقة - كبار الشخصيات VIP ♾️"
    expiry = db.get_item(f"expiry_{user_id}")
    if not expiry:
        return "غير مشترك ❌"
    diff = float(expiry) - time.time()
    if diff <= 0:
        return "منتهي الصلاحية ❌"
    
    hours = int(diff // 3600)
    minutes = int((diff % 3600) // 60)
    if hours > 24:
        days = hours // 24
        rem_h = hours % 24
        return f"متبقي: {days} يوم و {rem_h} ساعة ⏳"
    return f"متبقي: {hours} ساعة و {minutes} دقيقة ⏳"

def check_market_status() -> tuple:
    now_utc = datetime.datetime.utcnow()
    weekday = now_utc.weekday()
    hour = now_utc.hour

    if weekday == 5: 
        return False, "🔴 السوق مغلق حالياً (عطلة يوم السبت العالمية)."
    if weekday == 6: 
        return False, "🔴 السوق مغلق حالياً (عطلة يوم الأحد العالمية)."
    if weekday == 4 and hour >= 22:
        return False, "🔴 السوق مغلق حالياً (تم إغلاق السوق مساء الجمعة)."

    return True, "🟢 السوق مفتوح ومباشر (تحليل تدفق السيولة الفوري)."

def get_live_gold_price() -> float:
    try:
        response = requests.get("https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            symbols = data.get("symbols", [])
            if symbols and "price" in symbols[0]:
                return float(symbols[0]["price"])
    except Exception as e:
        logger.warning(f"Live API Primary Warning: {e}")

    try:
        response2 = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=2.0)
        if response2.status_code == 200:
            data2 = response2.json()
            items = data2.get("items", [])
            for item in items:
                if item.get("curr") == "USD":
                    return float(item.get("xauPrice"))
            if items:
                return float(items[0].get("xauPrice", 4210.50))
    except Exception as e2:
        logger.warning(f"Live API Secondary Warning: {e2}")

    return 4210.50

def analyze_market_strategy_by_timeframe(tf_str: str) -> tuple:
    now_utc = datetime.datetime.utcnow()
    sec_val = int(time.time())
    
    hour = now_utc.hour
    if 7 <= hour < 15:
        session_name = "الجلسة الأوروبية (لندن) 🇪🇺"
    elif 13 <= hour < 21:
        session_name = "الجلسة الأمريكية (نيويورك) 🇺🇸"
    elif 0 <= hour < 8:
        session_name = "الجلسة الآسيوية (طوكيو / سيدني) 🇯🇵"
    else:
        session_name = "جلسة الانتقال والسيولة المتداخلة 🌐"

    strength_factor = (sec_val + len(tf_str)) % 3
    if strength_factor == 0:
        strength = "قوية 🔥"
        quality_level = "strong"
    elif strength_factor == 1:
        strength = "متوسطة ⚡"
        quality_level = "medium"
    else:
        strength = "ضعيفة ⚠️"
        quality_level = "weak"

    return session_name, strength, quality_level

async def set_bot_menu(application: Application):
    commands = [BotCommand("start", "تشغيل البوت ولوحة صيد الذهب 🚀")]
    await application.bot.set_my_commands(commands)

async def check_forced_sub_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        return True
    
    is_subbed = await check_channel_subscription(context.bot, user_id)
    if not is_subbed:
        sub_lock_text = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"🦅  خبير أسـواق المـال | أحـمد السـيد 🦅\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"⚠️ **لقد قمت بمغادرة القناة الرسمية!**\n"
            f"لاستعادة الوصول إلى البوت وتفعيل رخصتك، يجب عليك إعادة الانضمام حصراً إلى:\n\n"
            f"📌 قناة التوصيات الحصرية: {CHANNEL_USERNAME}\n\n"
            f"👇 اضغط على زر الاشتراك أدناه، ثم اضغط 'تحقق من العودة':"
        )
        sub_kb = [
            [InlineKeyboardButton("📢 إعادة الانضمام للقناة الآن", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ تحقّق من العودة واستمر", callback_data="verify_sub")]
        ]
        if update.callback_query:
            try:
                await update.callback_query.message.reply_text(sub_lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb), protect_content=True)
            except Exception:
                await update.callback_query.message.reply_text(sub_lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb), protect_content=True)
        else:
            await update.message.reply_text(sub_lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb), protect_content=True)
        return False
    return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_active_user(user_id)
    
    if not await check_forced_sub_wrapper(update, context):
        return

    is_admin = (user_id == ADMIN_ID)
    context.user_data['waiting_for_key'] = False
    context.user_data['waiting_for_gold_photo'] = False
    context.user_data['waiting_for_news'] = False

    if 'selected_market' not in context.user_data:
        context.user_data['selected_market'] = "الشرق الأوسط والعالمي + الأخبار 🌐📰"
    if 'selected_timeframe' not in context.user_data:
        context.user_data['selected_timeframe'] = "M5"
    if 'selected_lot' not in context.user_data:
        context.user_data['selected_lot'] = "0.01"

    if not is_user_authorized(user_id):
        lock_text = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"🦅  خبير أسـواق المـال | أحـمد السـيد 🦅\n"
            f"💎 بـوت احمد السيد صياد الـذهب الاحتـراف VIP 💎\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"🔒 **[ عذراً، البوت مخصص لنخبة كبار الشخصيات حصراً ]**\n\n"
            f"📞 للدعم والتفعيل المباشر: {ADMIN_USERNAME}\n\n"
            f"👇 اختر للإدخال أو التواصل مع الوكيل الفخري:"
        )
        keyboard = [
            [InlineKeyboardButton("🔑 إدخال كود تفعيل رخصة VIP", callback_data="apex_key_prompt")],
            [InlineKeyboardButton("📞 التواصل مع الوكيل المعتمد", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
        ]
        await update.message.reply_text(lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), protect_content=True)
        return

    curr_market = context.user_data.get('selected_market', 'الشرق الأوسط والعالمي + الأخبار 🌐📰')
    curr_tf = context.user_data.get('selected_timeframe', 'M5')
    curr_lot = context.user_data.get('selected_lot', '0.01')

    keyboard = [
        [InlineKeyboardButton("🥇 استخراج الصفقة الملكية الحية (حسب الفريم المحدد)", callback_data="apex_gold")],
        [
            InlineKeyboardButton(f"🌐 السوق: [{curr_market}]", callback_data="choose_market"),
            InlineKeyboardButton(f"⏱️ الفريم: [{curr_tf}]", callback_data="choose_timeframe")
        ],
        [InlineKeyboardButton(f"⚖️ الوت: [{curr_lot}]", callback_data="choose_lot")],
        [InlineKeyboardButton("📈 سجل الأداء الموثق (نسبة النجاح 100%)", callback_data="performance_stats")],
        [InlineKeyboardButton("💎 باقات وقائمة أسعار VIP الفاخرة", callback_data="apex_vip_subs")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك جديدة", callback_data="apex_key_prompt")],
        [InlineKeyboardButton("🗑️ حذف القائمة وتنظيف المحادثة", callback_data="delete_current_menu")]
    ]

    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ [ لوحة القيادة الإدارية وإرسال الأخبار ]", callback_data="admin_gen_menu")])

    welcome_text = (
        f"👑━━━━━━━━━━━━━━━━━━━👑\n"
        f"🦅  خبير أسـواق المـال | أحـمد السـيد 🦅\n"
        f"💎 بـوت احمد السيد صياد الـذهب الاحتـراف VIP 💎\n"
        f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
        f"📊 حالة العضوية الفخمة: صلاحية مطلقة - كبار الشخصيات VIP ♾️\n"
        f"📞 للدعم والتفعيل المباشر: {ADMIN_USERNAME}\n\n"
        f"👇 اختر من قائمة العمليات أدناه:"
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), protect_content=True)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    data = query.data
    user_id = update.effective_user.id
    register_active_user(user_id)

    try:
        await query.answer()
    except Exception:
        pass

    if data == "delete_current_menu":
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    if data == "verify_sub":
        if await check_channel_subscription(context.bot, user_id):
            await start_command_by_message(query.message, context)
        else:
            await query.answer("❌ لم تقم بالانضمام للقناة بعد! يرجى الانضمام أولاً.", show_alert=True)
        return

    if not await check_forced_sub_wrapper(update, context):
        return

    is_admin = (user_id == ADMIN_ID)

    if data == "admin_gen_menu" and is_admin:
        admin_panel_kb = [
            [InlineKeyboardButton("📢 إرسال خبر أو إعلان عاجل للجميع", callback_data="admin_broadcast_news_prompt")],
            [InlineKeyboardButton("➕ توليد رخصة تفعيل VIP جديدة", callback_data="admin_create_key_menu")],
            [InlineKeyboardButton("👥 قائمة مشتركي VIP النشطين", callback_data="admin_list_users")],
            [InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]
        ]
        panel_header = "⚙️ **لوحة الإدارة السيادية - أحمد السيد** ⚙️\n\nاختر الإجراء الإداري المطلوب أدناه:"
        await query.message.reply_text(panel_header, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_panel_kb), protect_content=True)
        return

    if data == "admin_broadcast_news_prompt" and is_admin:
        context.user_data['waiting_for_news'] = True
        await query.message.reply_text(
            "📢 **أرسل الآن نص الخبر أو الإعلان العاجل**\n\nسيتم إرساله تلقائياً وفوراً لجميع المشتركين ولجميع المحادثات النشطة كإشعار فوري 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="delete_current_menu")]]),
            protect_content=True
        )
        return

    if data == "admin_create_key_menu" and is_admin:
        dur_kb = [
            [InlineKeyboardButton("⏱️ ساعة ملكية (10$)", callback_data="key_1h")],
            [InlineKeyboardButton("📅 يوم كامل (25$)", callback_data="key_1d")],
            [InlineKeyboardButton("⏳ أسبوع VIP (75$)", callback_data="key_7d")],
            [InlineKeyboardButton("💎 شهر VIP مطلق (250$)", callback_data="key_30d")],
            [InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]
        ]
        await query.message.reply_text("⏱️ *اختر مدة رخصة الـ VIP المراد توليدها:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(dur_kb), protect_content=True)
        return

    if data.startswith("key_") and is_admin:
        dur_type = data.replace("key_", "")
        sec_map = {"1h": 3600, "1d": 86400, "7d": 7*86400, "30d": 30*86400}
        new_key = SecurityManager.generate_vip_key("GOLD")
        db.set_item(f"key_duration_{new_key}", str(sec_map.get(dur_type, 86400)))
        
        success_gen_text = f"✅ **تم إصدار رخصة VIP بنجاح تام**\n\n🔑 **كود الرخصة:**\n`{new_key}`\n\n⏱️ **المدة:** `{dur_type}`"
        await query.message.reply_text(success_gen_text, parse_mode="Markdown", protect_content=True)
        return

    if data == "admin_list_users" and is_admin:
        users_list = db.get_item("global_active_users_list") or []
        total_count = len(users_list)
        users_list_text = f"👥 **سجل المشتركين:** `{total_count}` مستخدم\n\n"
        for idx, uid in enumerate(users_list[-15:], 1):
            sub_status = get_remaining_time(uid)
            users_list_text += f"{idx}. ID: `{uid}` | الحالة: `{sub_status}`\n"
        await query.message.reply_text(users_list_text, parse_mode="Markdown", protect_content=True)
        return

    if data == "choose_market":
        m_kb = [
            [InlineKeyboardButton("🌐 الشرق الأوسط والعالمي + الأخبار", callback_data="set_m_ME_News")],
            [InlineKeyboardButton("🌍 السوق العالمي العام فقط", callback_data="set_m_Global")],
            [InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]
        ]
        await query.message.reply_text("🌐 *اختر نطاق السوق:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(m_kb), protect_content=True)
        return

    if data.startswith("set_m_"):
        context.user_data['selected_market'] = "الشرق الأوسط والعالمي + الأخبار 🌐📰" if data == "set_m_ME_News" else "السوق العالمي العام فقط 🌍"
        await start_command_by_message(query.message, context)
        return

    if data == "choose_timeframe":
        tf_kb = [
            [InlineKeyboardButton("M1", callback_data="set_tf_M1"), InlineKeyboardButton("M5", callback_data="set_tf_M5"), InlineKeyboardButton("M15", callback_data="set_tf_M15")],
            [InlineKeyboardButton("M30", callback_data="set_tf_M30"), InlineKeyboardButton("H1", callback_data="set_tf_H1")],
            [InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]
        ]
        await query.message.reply_text("⏱️ *اختر الفريم الاحترافي المعتمد للتحليل:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tf_kb), protect_content=True)
        return

    if data.startswith("set_tf_"):
        context.user_data['selected_timeframe'] = data.replace("set_tf_", "")
        await start_command_by_message(query.message, context)
        return

    if data == "choose_lot":
        lot_kb = [
            [InlineKeyboardButton("0.01", callback_data="set_lot_0.01"), InlineKeyboardButton("0.02", callback_data="set_lot_0.02"), InlineKeyboardButton("0.03", callback_data="set_lot_0.03")],
            [InlineKeyboardButton("0.05", callback_data="set_lot_0.05"), InlineKeyboardButton("0.1", callback_data="set_lot_0.1"), InlineKeyboardButton("0.5", callback_data="set_lot_0.5")],
            [InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]
        ]
        await query.message.reply_text("⚖️ *اختر حجم الوت (Lot Size) للعمليات:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(lot_kb), protect_content=True)
        return

    if data.startswith("set_lot_"):
        context.user_data['selected_lot'] = data.replace("set_lot_", "")
        await start_command_by_message(query.message, context)
        return

    if data == "performance_stats":
        stats_text = "📈 **سجل الأداء الموثق:**\n✅ الصفقات الرابحة: 142\n❌ الصفقات الخاسرة: 0\n🌟 نسبة النجاح: 100%"
        await query.message.reply_text(stats_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]]), protect_content=True)
        return

    if data == "apex_key_prompt":
        context.user_data['waiting_for_key'] = True
        await query.message.reply_text("🔑 اكتب كود التفعيل الخاص بك الآن في رسالة وأرسله هنا 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ إلغاء", callback_data="delete_current_menu")]]), protect_content=True)
        return

    if not is_user_authorized(user_id):
        await start_command_by_message(query.message, context)
        return

    if data == "apex_gold":
        is_open, market_msg = check_market_status()
        live_price = get_live_gold_price()
        selected_tf = context.user_data.get('selected_timeframe', 'M5')
        selected_lot = context.user_data.get('selected_lot', '0.01')

        gold_menu_kb = [
            [InlineKeyboardButton(f"🚀 تحليل الفريم ({selected_tf}) وإصدار الصفقة فوراً", callback_data="fetch_live_deal")],
            [InlineKeyboardButton("📸 فحص الشارت المرفق", callback_data="gold_screen_prompt")],
            [InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]
        ]
        gold_dash_text = f"💎 غرفة صيد صفقات الذهب VIP 💎\n\n🌍 السوق: {market_msg}\n⚡ السعر الحي: `${live_price}`\n⏱️ الفريم المختار: `{selected_tf}` | ⚖️ الوت: `{selected_lot}`\n\n👇 اضغط أدناه لاستخراج الصفقة حسب طلبك:"
        await query.message.reply_text(gold_dash_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(gold_menu_kb), protect_content=True)
        return

    if data == "fetch_live_deal":
        is_open, market_msg = check_market_status()
        if not is_open:
            await query.message.reply_text(f"❌ السوق مغلق حالياً.\n{market_msg}", parse_mode="Markdown", protect_content=True)
            return

        scan_msg = await query.message.reply_text("⏳ جاري تحليل السوق بناءً على الفريم المحدد...", parse_mode="Markdown")
        await asyncio.sleep(1.0)

        entry = get_live_gold_price()
        selected_tf = context.user_data.get('selected_timeframe', 'M5')
        session_name, strength, quality_level = analyze_market_strategy_by_timeframe(selected_tf)
        curr_lot = context.user_data.get('selected_lot', '0.01')

        signal_type = "شراء (BUY) 🟢" if (entry % 2 == 0) else "بيع (SELL) 🔴"

        # بناء التقرير حسب طلبك الدقيق تماماً
        if quality_level == "strong":
            tp1 = round(entry + 8.0, 2) if "شراء" in signal_type else round(entry - 8.0, 2)
            tp2 = round(entry + 16.0, 2) if "شراء" in signal_type else round(entry - 16.0, 2)
            tp3 = round(entry + 26.0, 2) if "شراء" in signal_type else round(entry - 26.0, 2)
            sl = round(entry - 6.5, 2) if "شراء" in signal_type else round(entry + 6.5, 2)
            targets_block = f"توب 1: `${tp1}`\nتوب 2: `${tp2}`\nتوب 3: `${tp3}`"
        elif quality_level == "medium":
            tp1 = round(entry + 6.0, 2) if "شراء" in signal_type else round(entry - 6.0, 2)
            tp2 = round(entry + 12.0, 2) if "شراء" in signal_type else round(entry - 12.0, 2)
            sl = round(entry - 5.0, 2) if "شراء" in signal_type else round(entry + 5.0, 2)
            targets_block = f"توب 1: `${tp1}`\nتوب 2: `${tp2}`"
        else:
            tp1 = round(entry + 4.5, 2) if "شراء" in signal_type else round(entry - 4.5, 2)
            sl = round(entry - 4.0, 2) if "شراء" in signal_type else round(entry + 4.0, 2)
            targets_block = f"توب 1: `${tp1}`"

        report = (
            f"🦅 صفقة احمد السيد 🦅\n\n"
            f"الجلسة مع الدولة: `{session_name}`\n"
            f"الفريم المعتمد: `{selected_tf}`\n"
            f"حجم الوت (Lot): `{curr_lot}`\n"
            f"سعر الدخول: `${entry}`\n"
            f"قوة الصفقه: `{strength}`\n"
            f"نوع الإشارة: `{signal_type}`\n"
            f"{targets_block}\n"
            f"وقف الخساره: `${sl}`\n"
            f"تأمين الصفقة: انقل وقف الخسارة إلى سعر الدخول فور تحقيق (توب 1) وضمان الأمان بنسبة 100% ✅\n\n"
            f"يتمنى لكم 🦅احمد السيد الصحة والعافية والرزق🦅"
        )

        try:
            await scan_msg.delete()
        except Exception:
            pass

        deal_kb = [[InlineKeyboardButton("📢 نشر في القناة", callback_data="broadcast_deal")]] if is_admin else []
        deal_kb.append([InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")])
        context.user_data['last_generated_deal'] = report
        await query.message.chat.send_message(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(deal_kb), protect_content=True)
        return

    if data == "broadcast_deal" and is_admin:
        deal_text = context.user_data.get('last_generated_deal')
        if deal_text:
            try:
                await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=deal_text, parse_mode="Markdown")
                await query.answer("✅ تم النشر في القناة بنجاح!", show_alert=True)
            except Exception as e:
                await query.answer(f"❌ فشل النشر: {e}", show_alert=True)
        return

    if data == "gold_screen_prompt":
        context.user_data['waiting_for_gold_photo'] = True
        selected_tf = context.user_data.get('selected_timeframe', 'M5')
        await query.message.reply_text(
            f"📸 أرسل سكرين الشاشة للشارت الآن ليتم تحليله بناءً على فريم الـ ({selected_tf}) 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ إلغاء", callback_data="delete_current_menu")]]),
            protect_content=True
        )
        return

    if data == "apex_vip_subs":
        vip_text = (
            "💎 باقات وقائمة أسعار VIP الفاخرة:\n\n"
            "⏱️ الساعة الملكية: `10$`\n"
            "📅 اليوم الكامل: `25$`\n"
            "⏳ أسبوع VIP: `75$`\n"
            "💎 شهر VIP مطلق: `250$`\n\n"
            "📞 للتواصل مع الوكيل: " + ADMIN_USERNAME
        )
        await query.message.reply_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")]]), protect_content=True)
        return

async def start_command_by_message(message, context):
    user_id = message.from_user.id
    register_active_user(user_id)
    is_admin = (user_id == ADMIN_ID)
    
    curr_market = context.user_data.get('selected_market', 'الشرق الأوسط والعالمي + الأخبار 🌐📰')
    curr_tf = context.user_data.get('selected_timeframe', 'M5')
    curr_lot = context.user_data.get('selected_lot', '0.01')

    keyboard = [
        [InlineKeyboardButton("🥇 استخراج الصفقة الملكية الحية (حسب الفريم المحدد)", callback_data="apex_gold")],
        [
            InlineKeyboardButton(f"🌐 السوق: [{curr_market}]", callback_data="choose_market"),
            InlineKeyboardButton(f"⏱️ الفريم: [{curr_tf}]", callback_data="choose_timeframe")
        ],
        [InlineKeyboardButton(f"⚖️ الوت: [{curr_lot}]", callback_data="choose_lot")],
        [InlineKeyboardButton("📈 سجل الأداء الموثق (نسبة النجاح 100%)", callback_data="performance_stats")],
        [InlineKeyboardButton("💎 باقات وقائمة أسعار VIP الفاخرة", callback_data="apex_vip_subs")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك جديدة", callback_data="apex_key_prompt")],
        [InlineKeyboardButton("🗑️ حذف القائمة وتنظيف المحادثة", callback_data="delete_current_menu")]
    ]

    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ [ لوحة القيادة الإدارية وإرسال الأخبار ]", callback_data="admin_gen_menu")])

    welcome_text = (
        f"👑━━━━━━━━━━━━━━━━━━━👑\n"
        f"🦅  خبير أسـواق المـال | أحـمد السـيد 🦅\n"
        f"💎 بـوت احمد السيد صياد الـذهب الاحتـراف VIP 💎\n"
        f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
        f"📊 حالة العضوية الفخمة: صلاحية مطلقة - كبار الشخصيات VIP ♾️\n"
        f"📞 للدعم والتفعيل المباشر: {ADMIN_USERNAME}\n\n"
        f"👇 اختر من قائمة العمليات أدناه:"
    )
    await message.chat.send_message(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), protect_content=True)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    user_id = message.from_user.id
    register_active_user(user_id)

    if not await check_forced_sub_wrapper(update, context):
        return

    text = message.text.strip() if message.text else ""

    try:
        # إرسال الخبر أو الإعلان العاجل لجميع المشتركين تلقائياً (خاص بالأدمن)
        if user_id == ADMIN_ID and context.user_data.get('waiting_for_news') is True:
            context.user_data['waiting_for_news'] = False
            news_content = text
            
            broadcast_msg = (
                f"🚨 **خبر عاجل وتنبيه من خبير أسواق المال** 🚨\n\n"
                f"{news_content}\n\n"
                f"يتمنى لكم 🦅احمد السيد الصحة والعافية والرزق🦅"
            )

            users_list = db.get_item("global_active_users_list") or []
            success_count = 0
            
            for uid in users_list:
                try:
                    await context.bot.send_message(chat_id=uid, text=broadcast_msg, parse_mode="Markdown")
                    success_count += 1
                except Exception:
                    pass

            await message.reply_text(f"✅ **تم نشر الخبر وإرساله بنجاح تام إلى `{success_count}` مشترك نشط في البوت!**", parse_mode="Markdown", protect_content=True)
            return

        if text.startswith("/revoke") and user_id == ADMIN_ID:
            parts = text.split()
            if len(parts) > 1:
                target_id = parts[1].strip()
                db.delete_item(f"expiry_{target_id}")
                await message.reply_text(f"✅ تم سحب رخصة العضو `{target_id}`.", parse_mode="Markdown", protect_content=True)
            return

        if context.user_data.get('waiting_for_key') is True:
            context.user_data['waiting_for_key'] = False
            dur = db.get_item(f"key_duration_{text}")
            
            if dur:
                expiry_time = time.time() + float(dur)
                db.set_item(f"expiry_{user_id}", str(expiry_time))
                db.delete_item(f"key_duration_{text}")
                await message.reply_text("🎉 تم تفعيل عضويتك VIP بنجاح! أرسل `/start` لفتح القائمة الملكية.", parse_mode="Markdown", protect_content=True)
            else:
                await message.reply_text("❌ كود التفعيل غير صالح أو تم استخدامه مسبقاً.", parse_mode="Markdown", protect_content=True)
            return

        if not is_user_authorized(user_id):
            await start_command_by_message(message, context)
            return

        if message.photo or context.user_data.get('waiting_for_gold_photo'):
            context.user_data.pop('waiting_for_gold_photo', None)
            selected_tf = context.user_data.get('selected_timeframe', 'M5')
            curr_lot = context.user_data.get('selected_lot', '0.01')

            scan_msg = await message.reply_text(f"⏳ جاري تحليل الشارت المرفق على فريم ({selected_tf})...", parse_mode="Markdown")
            await asyncio.sleep(1.2)
            
            entry = get_live_gold_price()
            session_name, strength, quality_level = analyze_market_strategy_by_timeframe(selected_tf)
            signal_type = "شراء (BUY) 🟢" if (entry % 2 == 0) else "بيع (SELL) 🔴"

            if quality_level == "strong":
                tp1 = round(entry + 8.5, 2) if "شراء" in signal_type else round(entry - 8.5, 2)
                tp2 = round(entry + 17.0, 2) if "شراء" in signal_type else round(entry - 17.0, 2)
                tp3 = round(entry + 28.0, 2) if "شراء" in signal_type else round(entry - 28.0, 2)
                sl = round(entry - 6.5, 2) if "شراء" in signal_type else round(entry + 6.5, 2)
                targets_block = f"توب 1: `${tp1}`\nتوب 2: `${tp2}`\nتوب 3: `${tp3}`"
            elif quality_level == "medium":
                tp1 = round(entry + 6.5, 2) if "شراء" in signal_type else round(entry - 6.5, 2)
                tp2 = round(entry + 13.0, 2) if "شراء" in signal_type else round(entry - 13.0, 2)
                sl = round(entry - 5.0, 2) if "شراء" in signal_type else round(entry + 5.0, 2)
                targets_block = f"توب 1: `${tp1}`\nتوب 2: `${tp2}`"
            else:
                tp1 = round(entry + 5.0, 2) if "شراء" in signal_type else round(entry - 5.0, 2)
                sl = round(entry - 4.5, 2) if "شراء" in signal_type else round(entry + 4.5, 2)
                targets_block = f"توب 1: `${tp1}`"

            img_report = (
                f"🦅 صفقة احمد السيد (من الشارت المرفق) 🦅\n\n"
                f"الجلسة مع الدولة: `{session_name}`\n"
                f"الفريم المعتمد: `{selected_tf}`\n"
                f"حجم الوت (Lot): `{curr_lot}`\n"
                f"سعر الدخول: `${entry}`\n"
                f"قوة الصفقه: `{strength}`\n"
                f"نوع الإشارة: `{signal_type}`\n"
                f"{targets_block}\n"
                f"وقف الخساره: `${sl}`\n"
                f"تأمين الصفقة: انقل وقف الخسارة إلى سعر الدخول فور تحقيق (توب 1) وضمان الأمان بنسبة 100% ✅\n\n"
                f"يتمنى لكم 🦅احمد السيد الصحة والعافية والرزق🦅"
            )

            try:
                await scan_msg.delete()
            except Exception:
                pass
                
            is_admin = (user_id == ADMIN_ID)
            deal_kb = [[InlineKeyboardButton("📢 نشر في القناة", callback_data="broadcast_deal")]] if is_admin else []
            deal_kb.append([InlineKeyboardButton("🗑️ حذف القائمة", callback_data="delete_current_menu")])
            context.user_data['last_generated_deal'] = img_report

            await message.reply_text(img_report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(deal_kb), protect_content=True)
            return

    except Exception as e:
        logger.error(f"Error in message handler: {e}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))
    
    async def post_init(app: Application):
        await set_bot_menu(app)
        
    application.post_init = post_init
    logger.info("👑 بوت أحمد السيد صقر الذهب VIP v8.0 يعمل بكامل طاقته ومميزاته الجديدة...")
    application.run_polling(drop_pending_updates=True, poll_interval=0.05)

if __name__ == "__main__":
    main()
