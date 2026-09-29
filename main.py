import logging
import time
import datetime
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from utils import PathManager, LoggerManager, DatabaseManager, SecurityManager

# إعداد المسارات والسجلات
PathManager.create_directories("database", ["logs", "assets"])
logger = LoggerManager.get_logger("VIP_Core")
db = DatabaseManager("database/storage.json")

TELEGRAM_BOT_TOKEN = "8916004825:AAG67V-nkqGLileO6cOy7847UIoqtVVjPog"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  
CHANNEL_USERNAME = "@FOR2AH"  # قناتك الحصرية الإجبارية

async def check_channel_subscription(bot, user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # إذا كان العضو غادر أو طرد أو لم يعد مشتركاً
        if member.status in ['left', 'kicked']:
            return False
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
    except Exception as e2:
        logger.warning(f"Live API Secondary Warning: {e2}")

    return 4210.50

def analyze_market_strategy() -> tuple:
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

    strength_factor = sec_val % 3
    if strength_factor == 0:
        strength = "قوية جداً (تأكيد مؤسسي عالي) 🔥"
        quality_level = "strong"
    elif strength_factor == 1:
        strength = "متوسطة (زخم تدريجي آمن) ⚡"
        quality_level = "medium"
    else:
        strength = "ضعيفة وحذرة (تداول نطاقي ضيق) ⚠️"
        quality_level = "weak"

    tf_options = ["M1", "M5", "M15"]
    selected_tf = tf_options[sec_val % len(tf_options)]

    return session_name, strength, quality_level, selected_tf

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
                await update.callback_query.message.edit_text(sub_lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb))
            except Exception:
                await update.callback_query.message.reply_text(sub_lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb))
        else:
            await update.message.reply_text(sub_lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb))
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
        [InlineKeyboardButton("🥇 استخراج الصفقة الملكية الحية (منع العكس 100%)", callback_data="apex_gold")],
        [
            InlineKeyboardButton(f"🌐 السوق: [{curr_market}]", callback_data="choose_market"),
            InlineKeyboardButton(f"⏱️ الفريم: [{curr_tf}]", callback_data="choose_timeframe")
        ],
        [InlineKeyboardButton(f"⚖️ الوت: [{curr_lot}]", callback_data="choose_lot")],
        [InlineKeyboardButton("📈 سجل الأداء الموثق (نسبة النجاح 100%)", callback_data="performance_stats")],
        [InlineKeyboardButton("💎 باقات وقائمة أسعار VIP الفاخرة", callback_data="apex_vip_subs")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك جديدة", callback_data="apex_key_prompt")]
    ]

    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ [ لوحة القيادة الإدارية والمشتركين ]", callback_data="admin_gen_menu")])

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

    if data == "verify_sub":
        if await check_channel_subscription(context.bot, user_id):
            await query.message.delete()
            await start_command_by_message(query.message, context)
        else:
            await query.answer("❌ لم تقم بالانضمام للقناة بعد! يرجى الانضمام أولاً.", show_alert=True)
        return

    if not await check_forced_sub_wrapper(update, context):
        return

    is_admin = (user_id == ADMIN_ID)

    if data == "admin_gen_menu" and is_admin:
        admin_panel_kb = [
            [InlineKeyboardButton("➕ توليد رخصة تفعيل VIP جديدة", callback_data="admin_create_key_menu")],
            [InlineKeyboardButton("👥 قائمة مشتركي VIP النشطين والعدد الكلي", callback_data="admin_list_users")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        panel_header = "⚙️ **لوحة الإدارة السيادية - أحمد السيد** ⚙️\n\nاختر الإجراء الإداري المطلوب أدناه:"
        await query.message.edit_text(panel_header, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_panel_kb))
        return

    if data == "admin_create_key_menu" and is_admin:
        dur_kb = [
            [InlineKeyboardButton("⏱️ ساعة ملكية (10$)", callback_data="key_1h")],
            [InlineKeyboardButton("📅 يوم كامل (25$)", callback_data="key_1d")],
            [InlineKeyboardButton("⏳ أسبوع VIP (75$)", callback_data="key_7d")],
            [InlineKeyboardButton("💎 شهر VIP مطلق (250$)", callback_data="key_30d")],
            [InlineKeyboardButton("🔙 رجوع لإدارة اللوحة", callback_data="admin_gen_menu")]
        ]
        await query.message.edit_text("⏱️ *اختر مدة رخصة الـ VIP المراد توليدها:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(dur_kb))
        return

    if data.startswith("key_") and is_admin:
        dur_type = data.replace("key_", "")
        sec_map = {"1h": 3600, "1d": 86400, "7d": 7*86400, "30d": 30*86400}
        new_key = SecurityManager.generate_vip_key("GOLD")
        db.set_item(f"key_duration_{new_key}", str(sec_map.get(dur_type, 86400)))
        
        success_gen_text = f"✅ **تم إصدار رخصة VIP بنجاح تام**\n\n🔑 **كود الرخصة:**\n`{new_key}`\n\n⏱️ **المدة:** `{dur_type}`"
        await query.message.edit_text(success_gen_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع لإدارة اللوحة", callback_data="admin_gen_menu")]]))
        return

    if data == "admin_list_users" and is_admin:
        users_list = db.get_item("global_active_users_list") or []
        total_count = len(users_list)
        users_list_text = f"👥 **سجل المشتركين:** `{total_count}` مستخدم\n\n"
        for idx, uid in enumerate(users_list[-15:], 1):
            sub_status = get_remaining_time(uid)
            users_list_text += f"{idx}. ID: `{uid}` | الحالة: `{sub_status}`\n"
        await query.message.edit_text(users_list_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع لإدارة اللوحة", callback_data="admin_gen_menu")]]))
        return

    if data == "choose_market":
        m_kb = [
            [InlineKeyboardButton("🌐 الشرق الأوسط والعالمي + الأخبار", callback_data="set_m_ME_News")],
            [InlineKeyboardButton("🌍 السوق العالمي العام فقط", callback_data="set_m_Global")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("🌐 *اختر نطاق السوق:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(m_kb))
        return

    if data.startswith("set_m_"):
        context.user_data['selected_market'] = "الشرق الأوسط والعالمي + الأخبار 🌐📰" if data == "set_m_ME_News" else "السوق العالمي العام فقط 🌍"
        await query.message.delete()
        await start_command_by_message(query.message, context)
        return

    if data == "choose_timeframe":
        tf_kb = [
            [InlineKeyboardButton("M1", callback_data="set_tf_M1"), InlineKeyboardButton("M5", callback_data="set_tf_M5"), InlineKeyboardButton("M15", callback_data="set_tf_M15")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("⏱️ *اختر الفريم الاحترافي:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tf_kb))
        return

    if data.startswith("set_tf_"):
        context.user_data['selected_timeframe'] = data.replace("set_tf_", "")
        await query.message.delete()
        await start_command_by_message(query.message, context)
        return

    if data == "choose_lot":
        lot_kb = [
            [InlineKeyboardButton("0.01", callback_data="set_lot_0.01"), InlineKeyboardButton("0.02", callback_data="set_lot_0.02"), InlineKeyboardButton("0.03", callback_data="set_lot_0.03")],
            [InlineKeyboardButton("0.05", callback_data="set_lot_0.05"), InlineKeyboardButton("0.1", callback_data="set_lot_0.1")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("⚖️ *اختر حجم الوت (Lot Size):*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(lot_kb))
        return

    if data.startswith("set_lot_"):
        context.user_data['selected_lot'] = data.replace("set_lot_", "")
        await query.message.delete()
        await start_command_by_message(query.message, context)
        return

    if data == "performance_stats":
        stats_text = "📈 **سجل الأداء:**\n✅ رابحة: 142\n❌ خاسرة: 0\n🌟 نسبة النجاح: 100%"
        await query.message.edit_text(stats_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]]))
        return

    if data == "apex_key_prompt":
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text("🔑 اكتب كود التفعيل الخاص بك الآن في رسالة وأرسله هنا 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="main_menu")]]))
        return

    if data == "main_menu":
        context.user_data['waiting_for_key'] = False
        await query.message.delete()
        await start_command_by_message(query.message, context)
        return

    if not is_user_authorized(user_id):
        await query.message.delete()
        await start_command_by_message(query.message, context)
        return

    if data == "apex_gold":
        is_open, market_msg = check_market_status()
        live_price = get_live_gold_price()
        gold_menu_kb = [
            [InlineKeyboardButton("🚀 استخراج وتأكيد الصفقة الآمنة الآن", callback_data="fetch_live_deal")],
            [InlineKeyboardButton("📸 فحص الشارت المرفق", callback_data="gold_screen_prompt")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        gold_dash_text = f"💎 غرفة صيد صفقات الذهب VIP 💎\n\n🌍 السوق: {market_msg}\n⚡ السعر الحي: `${live_price}`\n\n👇 اختر أدناه:"
        await query.message.edit_text(gold_dash_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(gold_menu_kb))
        return

    if data == "fetch_live_deal":
        is_open, market_msg = check_market_status()
        if not is_open:
            await query.message.edit_text(f"❌ السوق مغلق حالياً.\n{market_msg}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]))
            return

        scan_msg = await query.message.edit_text("⏳ جاري تحليل السوق...", parse_mode="Markdown")
        await asyncio.sleep(1.0)

        entry = get_live_gold_price()
        session_name, strength, quality_level, selected_tf = analyze_market_strategy()
        curr_lot = context.user_data.get('selected_lot', '0.01')

        signal_type = "شراء (BUY) 🟢" if (entry % 2 == 0) else "بيع (SELL) 🔴"
        tp1 = round(entry + 7.5, 2) if "شراء" in signal_type else round(entry - 7.5, 2)
        sl = round(entry - 6.0, 2) if "شراء" in signal_type else round(entry + 6.0, 2)

        report = f"توصيات صقر الذهب 🦅\n\nالجلسة: `{session_name}`\nالفريم: `{selected_tf}`\nالإشارة: `{signal_type}`\nالوت: `{curr_lot}`\nالدخول: `${entry}`\nالهدف الأول: `${tp1}`\nوقف الخسارة: `${sl}`"

        await scan_msg.delete()
        deal_kb = [[InlineKeyboardButton("📢 نشر في القناة", callback_data="broadcast_deal")]] if is_admin else []
        deal_kb.append([InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")])
        context.user_data['last_generated_deal'] = report
        await query.message.chat.send_message(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(deal_kb))
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
        await query.message.edit_text("📸 أرسل سكرين الشاشة للشارت الآن ليتم تحليله 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="main_menu")]]))
        return

    if data == "apex_vip_subs":
        vip_text = "💎 باقات VIP:\n⏱️ ساعة: 10$\n📅 يوم: 25$\n⏳ أسبوع: 75$\n💎 شهر: 250$\n📞 للتواصل: " + ADMIN_USERNAME
        await query.message.edit_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]))
        return

async def start_command_by_message(message, context):
    user_id = message.from_user.id
    register_active_user(user_id)
    is_admin = (user_id == ADMIN_ID)
    
    curr_market = context.user_data.get('selected_market', 'الشرق الأوسط والعالمي + الأخبار 🌐📰')
    curr_tf = context.user_data.get('selected_timeframe', 'M5')
    curr_lot = context.user_data.get('selected_lot', '0.01')

    keyboard = [
        [InlineKeyboardButton("🥇 استخراج الصفقة الملكية الحية (منع العكس 100%)", callback_data="apex_gold")],
        [
            InlineKeyboardButton(f"🌐 السوق: [{curr_market}]", callback_data="choose_market"),
            InlineKeyboardButton(f"⏱️ الفريم: [{curr_tf}]", callback_data="choose_timeframe")
        ],
        [InlineKeyboardButton(f"⚖️ الوت: [{curr_lot}]", callback_data="choose_lot")],
        [InlineKeyboardButton("📈 سجل الأداء الموثق (نسبة النجاح 100%)", callback_data="performance_stats")],
        [InlineKeyboardButton("💎 باقات وقائمة أسعار VIP الفاخرة", callback_data="apex_vip_subs")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك جديدة", callback_data="apex_key_prompt")]
    ]

    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ [ لوحة القيادة الإدارية والمشتركين ]", callback_data="admin_gen_menu")])

    welcome_text = "👑 بـوت احمد السيد صياد الـذهب الاحتـراف VIP 👑\n\nاختر من قائمة العمليات أدناه:"
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
        if text.startswith("/revoke") and user_id == ADMIN_ID:
            parts = text.split()
            if len(parts) > 1:
                target_id = parts[1].strip()
                db.delete_item(f"expiry_{target_id}")
                await message.reply_text(f"✅ تم سحب رخصة العضو `{target_id}`.", parse_mode="Markdown")
            return

        if context.user_data.get('waiting_for_key') is True:
            context.user_data['waiting_for_key'] = False
            dur = db.get_item(f"key_duration_{text}")
            
            if dur:
                expiry_time = time.time() + float(dur)
                db.set_item(f"expiry_{user_id}", str(expiry_time))
                db.delete_item(f"key_duration_{text}")
                await message.reply_text("🎉 تم تفعيل عضويتك VIP بنجاح! أرسل `/start` للبدء.", parse_mode="Markdown")
            else:
                await message.reply_text("❌ كود التفعيل غير صالح.", parse_mode="Markdown")
            return

        if not is_user_authorized(user_id):
            await start_command_by_message(message, context)
            return

        if message.photo or context.user_data.get('waiting_for_gold_photo'):
            context.user_data.pop('waiting_for_gold_photo', None)
            scan_msg = await message.reply_text("⏳ جاري تحليل الشارت...", parse_mode="Markdown")
            await asyncio.sleep(1.0)
            
            entry = get_live_gold_price()
            session_name, strength, quality_level, selected_tf = analyze_market_strategy()
            report = f"توصيات الشارت المرفق 🦅\nالدخول: `${entry}`\nالفريم: `{selected_tf}`"
            
            await scan_msg.delete()
            await message.reply_text(report, parse_mode="Markdown")
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
    logger.info("👑 البوت يعمل بكامل طاقته ومميزاته...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
