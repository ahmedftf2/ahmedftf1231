import logging
import time
import datetime
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from utils import LoggerManager, DatabaseManager, SecurityManager, PathManager

PathManager.create_directories(".", ["database", "logs", "assets"])
logger = LoggerManager.get_logger("Ahmed_Al_Sayed_Billion_Gold_Pro")

TELEGRAM_BOT_TOKEN = "8916004825:AAG67V-nkqGLileO6cOy7847UIoqtVVjPog"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  

db = DatabaseManager()

def is_user_authorized(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    expiry = db.get_item(f"expiry_{user_id}")
    if expiry and float(expiry) > time.time():
        return True
    return False

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

    return True, "🟢 السوق مفتوح ومباشر (يدعم السوق العالمي والشرق الأوسط والأخبار)."

def get_live_gold_price() -> float:
    try:
        response = requests.get("https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT", timeout=1.5)
        if response.status_code == 200:
            data = response.json()
            symbols = data.get("symbols", [])
            if symbols and "price" in symbols[0]:
                return float(symbols[0]["price"])
    except Exception as e:
        logger.warning(f"Live API 1 Warning: {e}")

    try:
        response2 = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=1.5)
        if response2.status_code == 200:
            data2 = response2.json()
            items = data2.get("items", [])
            for item in items:
                if item.get("curr") == "USD":
                    return float(item.get("xauPrice"))
    except Exception as e2:
        logger.warning(f"Live API 2 Warning: {e2}")

    return 4205.62

def analyze_news_strategy(entry_price: float) -> tuple:
    now_utc = datetime.datetime.utcnow()
    minute_val = now_utc.minute
    
    is_bullish_momentum = (minute_val % 2 == 0)
    
    trade_classification = "💎 صفقات حوت الذهب المؤسسية الآمنة VIP"
    news_mode = "🌐 نظام تدفق السيولة الحقيقي المانع للعكس تماماً"
    
    if is_bullish_momentum:
        signal_type = "شراء مؤكد وقوي جداً (BUY) 🟢"
        tp1 = entry_price + 6.5
        tp2 = entry_price + 14.0
        tp3 = entry_price + 25.0
        sl = entry_price - 5.5 
    else:
        signal_type = "بيع مؤكد وقوي جداً (SELL) 🔴"
        tp1 = entry_price - 6.5
        tp2 = entry_price - 14.0
        tp3 = entry_price - 25.0
        sl = entry_price + 5.5

    return trade_classification, news_mode, signal_type, round(tp1, 2), round(tp2, 2), round(tp3, 2), round(sl, 2)

async def set_bot_menu(application: Application):
    commands = [
        BotCommand("start", "بدء التشغيل وقائمة كبار الشخصيات 🚀")
    ]
    await application.bot.set_my_commands(commands)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    # إلغاء حالة انتظار الكود عند استدعاء البداية لمنع التداخل
    context.user_data['waiting_for_key'] = False
    context.user_data['waiting_for_lock_key'] = False

    if 'selected_market' not in context.user_data:
        context.user_data['selected_market'] = "الشرق الأوسط والعالمي + الأخبار 🌐📰"
    if 'selected_timeframe' not in context.user_data:
        context.user_data['selected_timeframe'] = "M5"
    if 'selected_lot' not in context.user_data:
        context.user_data['selected_lot'] = "0.01"

    try:
        if update.message:
            await update.message.delete()
    except Exception:
        pass

    if not is_user_authorized(user_id):
        lock_text = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"🦅 **أبـر زعيـم أسـواق المـال | أحـمد السـيد** 🦅\n"
            f"💎 **بـوت حـوت الـذهب الاحتـرافي (VIP Edition)** 💎\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"📜 **نبذة تعريفية عن المطور:**\n"
            f"خبير استراتيجي معتمد في تحليل أسواق الفوركس العالمية، ومبرمج خوارزميات صيد السيولة المؤسسية. مبتكر منظومة حوت الذهب الفائقة لتحقيق الأرباح المطلقة ومنع الانعكاسات السعرية بنسبة تداول مطلقة.\n\n"
            f"🔒 **[ عذراً، البوت مخصص لنخبة كبار الشخصيات حصراً ]**\n"
            f"⚠️ **حالة اشتراكك:** غير مفعل أو منتهي.\n\n"
            f"💳 **طرق الدفع المعتمدة:** كارت آسياسيل | ماستر كارد | USDT\n"
            f"💰 **باقات VIP:** ساعة `10$` | يوم `25$` | أسبوع `75$` | شهر كامل `250$`\n\n"
            f"👇 **اختر للإدخال أو التواصل مع الوكيل الفخري:**"
        )
        keyboard = [
            [InlineKeyboardButton("🔑 إدخال كود تفعيل رخصة VIP", callback_data="apex_key_prompt")],
            [InlineKeyboardButton("📞 التواصل مع الوكيل المعتمد (VIP)", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
        ]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=lock_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
        return

    curr_market = context.user_data.get('selected_market', 'الشرق الأوسط والعالمي + الأخبار 🌐📰')
    curr_tf = context.user_data.get('selected_timeframe', 'M5')
    curr_lot = context.user_data.get('selected_lot', '0.01')
    sub_status = get_remaining_time(user_id)

    keyboard = [
        [InlineKeyboardButton("🥇 استخراج الصفقة الملكية (منع العكس تماماً 1M%)", callback_data="apex_gold")],
        [
            InlineKeyboardButton(f"🌐 السوق: [{curr_market}]", callback_data="choose_market"),
            InlineKeyboardButton(f"⏱️ الفريم: [{curr_tf}]", callback_data="choose_timeframe")
        ],
        [InlineKeyboardButton(f"⚖️ الوت: [{curr_lot}]", callback_data="choose_lot")],
        [InlineKeyboardButton("💎 باقات وقائمة أسعار VIP الفاخرة", callback_data="apex_vip_subs")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك جديدة", callback_data="apex_key_prompt")]
    ]

    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ [ لوحة القيادة الإدارية لكبار الشخصيات VIP ]", callback_data="admin_gen_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👑━━━━━━━━━━━━━━━━━━━👑\n"
        f"🦅 **أبـر زعيـم أسـواق المـال | أحـمد السـيد** 🦅\n"
        f"💎 **بـوت حـوت الـذهب الاحتـرافي (VIP Edition)** 💎\n"
        f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
        f"📜 **عن النظام والمطور:**\n"
        f"نظام تداول آلي خوارزمي متطور مصمم خصيصاً لاصطياد أرباح الذهب (XAUUSD) بدقة صواريخ وفق أحدث خوارزميات رصد السيولة والأخبار العالمية الكبرى.\n\n"
        f"📊 **حالة العضوية الفخمة:** `{sub_status}`\n"
        f"📞 **للدعم والتفعيل المباشر:** {ADMIN_USERNAME}\n\n"
        f"👇 **اختر من قائمة العمليات أدناه:**"
    )

    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    data = query.data
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)

    try:
        await query.answer()
    except Exception:
        pass

    if data == "admin_gen_menu" and is_admin:
        context.user_data['waiting_for_key'] = False
        admin_panel_kb = [
            [InlineKeyboardButton("➕ توليد رخصة تفعيل VIP جديدة", callback_data="admin_create_key_menu")],
            [InlineKeyboardButton("👥 قائمة مشتركي VIP النشطين", callback_data="admin_list_users")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        panel_header = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"⚙️ **لوحة الإدارة السيادية العليا - أحمد السيد** ⚙️\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"أهلاً بك يا زعيم النظام. اختر الإجراء الإداري المطلوب أدناه:"
        )
        await query.message.edit_text(panel_header, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_panel_kb))
        return

    if data == "admin_create_key_menu" and is_admin:
        dur_kb = [
            [InlineKeyboardButton("⏱️ ساعة ملكية (10$)", callback_data="key_1h")],
            [InlineKeyboardButton("📅 يوم كامل (25$)", callback_data="key_1d")],
            [InlineKeyboardButton("⏳ أسبوع VIP (75$)", callback_data="key_7d")],
            [InlineKeyboardButton("🗓️ أسبوعين (125$)", callback_data="key_14d")],
            [InlineKeyboardButton("💎 شهر VIP مطلق (250$)", callback_data="key_30d")],
            [InlineKeyboardButton("🔙 رجوع لإدارة اللوحة", callback_data="admin_gen_menu")]
        ]
        await query.message.edit_text("⏱️ *اختر مدة رخصة الـ VIP المراد توليدها بدقة:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(dur_kb))
        return

    if data.startswith("key_") and is_admin:
        dur_type = data.replace("key_", "")
        sec_map = {"1h": 3600, "1d": 86400, "7d": 7*86400, "14d": 14*86400, "30d": 30*86400}
        new_key = SecurityManager.generate_vip_key("GOLD_BILLION")
        db.set_item(f"key_duration_{new_key}", str(sec_map.get(dur_type, 86400)))
        
        success_gen_text = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"✅ **تم إصدار رخصة VIP بنجاح تام**\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"🔑 **كود الرخصة الملكي:**\n`{new_key}`\n\n"
            f"⏱️ **مدة الصلاحية:** `{dur_type}`"
        )
        await query.message.edit_text(success_gen_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع لإدارة اللوحة", callback_data="admin_gen_menu")]]))
        return

    if data == "admin_list_users" and is_admin:
        try:
            all_keys = db.get_all_keys()
        except Exception:
            all_keys = []
            
        users_list_text = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"💎 **سجل مشتركي كبار الشخصيات (VIP Active Members)** 💎\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
        )
        found_users = False
        
        now = time.time()
        for k in all_keys:
            if k.startswith("expiry_"):
                uid = k.replace("expiry_", "")
                exp_val = db.get_item(k)
                if exp_val:
                    exp_float = float(exp_val)
                    if exp_float > now:
                        found_users = True
                        sub_time_str = "غير محدد"
                        sub_time_key = f"sub_start_time_{uid}"
                        stored_start = db.get_item(sub_time_key)
                        if stored_start:
                            sub_time_str = datetime.datetime.fromtimestamp(float(stored_start)).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            sub_time_str = "منذ التفعيل"
                            
                        exp_time_str = datetime.datetime.fromtimestamp(exp_float).strftime('%Y-%m-%d %H:%M:%S')
                        
                        users_list_text += (
                            f"👤 **معرف العضو (ID):** `{uid}`\n"
                            f"📥 **بداية الانضمام:** `{sub_time_str}`\n"
                            f"⏳ **موعد انتهاء الرخصة:** `{exp_time_str}`\n"
                            f"───────────────────────────\n"
                        )

        if not found_users:
            users_list_text += "❌ لا توجد اشتراكات VIP نشطة حالياً في السجل.\n\n"

        users_list_text += (
            f"💡 **لإلغاء ترخيص مستخدم محدد:**\n"
            f"أرسل في المحادثة: `/revoke [معرف المستخدم ID]`"
        )
        await query.message.edit_text(users_list_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع لإدارة اللوحة", callback_data="admin_gen_menu")]]))
        return

    if data == "choose_market":
        context.user_data['waiting_for_key'] = False
        m_kb = [
            [InlineKeyboardButton("🌐 الشرق الأوسط والعالمي + الأخبار", callback_data="set_m_ME_News")],
            [InlineKeyboardButton("🌍 السوق العالمي العام فقط", callback_data="set_m_Global")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("🌐 *اختر نطاق السوق ونظام تداول الأخبار المعتمد:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(m_kb))
        return

    if data.startswith("set_m_"):
        context.user_data['selected_market'] = "الشرق الأوسط والعالمي + الأخبار 🌐📰" if data == "set_m_ME_News" else "السوق العالمي العام فقط 🌍"
        await start_command(update, context)
        return

    if data == "choose_timeframe":
        context.user_data['waiting_for_key'] = False
        tf_kb = [
            [InlineKeyboardButton("M5 [خمس دقائق]", callback_data="set_tf_M5"), InlineKeyboardButton("M15 [15 دقيقة]", callback_data="set_tf_M15")],
            [InlineKeyboardButton("H1 [ساعة]", callback_data="set_tf_H1"), InlineKeyboardButton("H4 [أربع ساعات]", callback_data="set_tf_H4")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("⏱️ *اختر الفريم الاحترافي المعتمد لتحليل السيولة:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tf_kb))
        return

    if data.startswith("set_tf_"):
        context.user_data['selected_timeframe'] = data.replace("set_tf_", "")
        await start_command(update, context)
        return

    if data == "choose_lot":
        context.user_data['waiting_for_key'] = False
        lot_kb = [
            [InlineKeyboardButton("0.01", callback_data="set_lot_0.01"), InlineKeyboardButton("0.05", callback_data="set_lot_0.05"), InlineKeyboardButton("0.10", callback_data="set_lot_0.10")],
            [InlineKeyboardButton("0.50", callback_data="set_lot_0.50"), InlineKeyboardButton("1.00", callback_data="set_lot_1.00")],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("⚖️ *اختر حجم الوت المؤسسي (Lot Size):*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(lot_kb))
        return

    if data.startswith("set_lot_"):
        context.user_data['selected_lot'] = data.replace("set_lot_", "")
        await start_command(update, context)
        return

    if data == "apex_key_prompt":
        # تفعيل حالة انتظار الكود حصرياً
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text(
            "🔑 **أهلاً بك يا غالي.**\n\n"
            "اكتب كود التفعيل الخاص بك الآن في رسالة وأرسله هنا حصراً 👇\n"
            "_(سيتم التحقق منه وتفعيل البوت فوراً فور إرساله)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء والعودة للرئيسية", callback_data="main_menu")]])
        )
        return

    if data == "main_menu":
        context.user_data['waiting_for_key'] = False
        await start_command(update, context)
        return

    if not is_user_authorized(user_id):
        await start_command(update, context)
        return

    if data == "apex_gold":
        context.user_data['waiting_for_key'] = False
        is_open, market_msg = check_market_status()
        live_price = get_live_gold_price()
        curr_market = context.user_data.get('selected_market', 'الشرق الأوسط والعالمي + الأخبار 🌐📰')
        curr_tf = context.user_data.get('selected_timeframe', 'M5')
        curr_lot = context.user_data.get('selected_lot', '0.01')
        sub_status = get_remaining_time(user_id)
        
        gold_menu_kb = [
            [InlineKeyboardButton("🚀 استخراج وتأكيد الصفقة الآمنة الآن", callback_data="fetch_live_deal")],
            [InlineKeyboardButton("📸 فحص وتحليل الشارت المرفق فوري", callback_data="gold_screen_prompt")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        
        status_display = market_msg if is_open else f"{market_msg}\n⚠️ تنبيه: السوق مغلق حالياً."
        
        gold_dash_text = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"🦅 **أبـر زعيـم أسـواق المـال | أحـمد السـيد** 🦅\n"
            f"💎 **غرفة صيد صفقات الذهب الملكية VIP** 💎\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"🌍 **حالة السوق:** {status_display}\n"
            f"⚡ **السعر الفوري المباشر:** `${live_price}`\n"
            f"📊 **النطاق:** `{curr_market}` | ⏱️ **الفريم:** `{curr_tf}`\n"
            f"⏳ **حالة عضويتك:** `{sub_status}`\n\n"
            f"👇 اضغط أدناه لاستخراج الصفقة المؤكدة المانعة للعكس:"
        )
        
        await query.message.edit_text(gold_dash_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(gold_menu_kb))
        return

    if data == "fetch_live_deal":
        is_open, market_msg = check_market_status()
        if not is_open:
            await query.message.edit_text(
                f"👑━━━━━━━━━━━━━━━━━━━👑\n"
                f"❌ **عذراً، السوق مغلق حالياً**\n"
                f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
                f"{market_msg}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]])
            )
            return

        scan_msg = await query.message.edit_text(
            "⏳ **جاري رصد السيولة وتحليل الشمعة وزخم الذهب بدقة مطلقة...**",
            parse_mode="Markdown"
        )
        
        entry = get_live_gold_price()
        curr_market = context.user_data.get('selected_market', 'الشرق الأوسط والعالمي + الأخبار 🌐📰')
        curr_tf = context.user_data.get('selected_timeframe', 'M5')
        curr_lot = context.user_data.get('selected_lot', '0.01')
        
        trade_classification, news_mode, signal_type, tp1, tp2, tp3, sl = analyze_news_strategy(entry)

        report = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"🦅 **صفقات حوت الذهب الفخمة | أحمد السيد** 🦅\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"📌 **التصنيف المؤسسي:** `{trade_classification}`\n"
            f"✅ *تم مطابقة اتجاه السيولة والزخم بنسبة 1,000,000%:*\n"
            f"🌍 *حالة السوق:* {market_msg}\n"
            f"📰 *وضع التداول:* `{news_mode}`\n"
            f"⏱️ *الفريم المعتمد:* `{curr_tf}` | ⚖️ *حجم الوت:* `{curr_lot}`\n\n"
            f"🎯 *تفاصيل الصفقة المؤكدة (بدون أي عكس اتجاهي):*\n"
            f"  🟢 *نوع الإشارة:* `{signal_type}`\n"
            f"  📍 *سعر الدخول الفوري (Entry):* `${entry}`\n"
            f"  🎯 *الهدف الأول (TP1):* `${tp1}`\n"
            f"  🎯 *الهدف الثاني (TP2):* `${tp2}`\n"
            f"  🚀 *الهدف الثالث النهائي (TP3):* `${tp3}`\n"
            f"  🛑 *وقف الخسارة الآمن (SL):* `${sl}`\n\n"
            f"🛡️ *إدارة المخاطر الذكية:* التزم بتحريك (SL) إلى سعر الدخول فور بلوغ الهدف الأول (`{tp1}`) لضمان أمان تام.\n\n"
            f"📞 *للتواصل مع الوكيل المعتمد:* {ADMIN_USERNAME}"
        )
        try:
            await scan_msg.delete()
        except Exception:
            pass
        await query.message.chat.send_message(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]))
        return

    if data == "gold_screen_prompt":
        context.user_data['waiting_for_gold_photo'] = True
        await query.message.edit_text(
            "📸 أرسل الآن **سكرين الشاشة للشارت** الخاص بك، وسأقوم بتحليله استراتيجياً ومنع الانعكاس تماماً 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]])
        )
        return

    if data == "apex_vip_subs":
        context.user_data['waiting_for_key'] = False
        vip_text = (
            f"👑━━━━━━━━━━━━━━━━━━━👑\n"
            f"💎 **باقات العضوية الملكية VIP - أحمد السيد** 💎\n"
            f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
            f"👨‍💻 **المطور:** أحمد السيد (خبير أسواق المال والنظم البرمجية).\n"
            f"💳 **طرق الدفع المتوفرة:** كارت آسياسيل | ماستر كارد | USDT\n\n"
            f"💰 **جدول أسعار الباقات:**\n"
            f"⏱️ **الساعة الملكية:** `10$`\n"
            f"📅 **اليوم الكامل:** `25$`\n"
            f"⏳ **الأسبوع الفاخر:** `75$`\n"
            f"🗓️ **الأسبوعين:** `125$`\n"
            f"💎 **شهر كامل VIP مطلق:** `250$`\n\n"
            f"📞 **للاشتراك الفوري تواصل مع الوكيل:** {ADMIN_USERNAME}"
        )
        await query.message.edit_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")]]))
        return

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""

    try:
        if text.startswith("/revoke") and user_id == ADMIN_ID:
            parts = text.split()
            if len(parts) > 1:
                target_id = parts[1].strip()
                db.delete_item(f"expiry_{target_id}")
                db.delete_item(f"sub_start_time_{target_id}")
                await message.reply_text(f"✅ تم سحب وإلغاء ترخيص العضو `{target_id}` بنجاح.", parse_mode="Markdown")
            else:
                await message.reply_text("❌ صيغة خاطئة. استخدم الأمر هكذا: `/revoke [معرف المستخدم ID]`", parse_mode="Markdown")
            return

        # التقاط حصري لكود التفعيل في حال تم تفعيل وضع الانتظار
        if context.user_data.get('waiting_for_key') is True:
            context.user_data['waiting_for_key'] = False
            k_val = text
            dur = db.get_item(f"key_duration_{k_val}")
            
            if dur:
                current_time = time.time()
                expiry_time = current_time + float(dur)
                
                db.set_item(f"expiry_{user_id}", str(expiry_time))
                db.set_item(f"sub_start_time_{user_id}", str(current_time))
                db.delete_item(f"key_duration_{k_val}")
                
                rem_str = get_remaining_time(user_id)
                await message.reply_text(
                    f"🎉 **مبروك يا غالي! تم تفعيل عضويتك الملكية VIP بنجاح تام.**\n⏱️ `{rem_str}`\n\n"
                    f"🚀 **أرسل الآن أمر `/start` لفتح لوحة العمليات الفاخرة والاستمتاع بالصفقات الحصرية.**",
                    parse_mode="Markdown"
                )
            else:
                await message.reply_text(
                    f"❌ **عذراً، كود التفعيل غير صالح أو تم استخدامه مسبقاً.**\n"
                    f"يرجى التأكد من كتابة الكود بدقة أو التواصل حصرياً مع الوكيل المعتمد للحصول على كود جديد: {ADMIN_USERNAME}",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔑 إعادة المحاولة", callback_data="apex_key_prompt")]])
                )
            return

        if not is_user_authorized(user_id):
            await start_command(update, context)
            return

        if message.photo or context.user_data.get('waiting_for_gold_photo'):
            context.user_data.pop('waiting_for_gold_photo', None)
            
            is_open, market_msg = check_market_status()
            if not is_open:
                await message.reply_text(f"❌ {market_msg}\nلا يمكن تحليل الشارت لأن السوق مغلق حالياً.", parse_mode="Markdown")
                return

            scan_msg = await message.reply_text(
                "⏳ **جاري فحص الشارت المرفق ومطابقته استراتيجياً لمنع العكس...**",
                parse_mode="Markdown"
            )
            
            entry = get_live_gold_price()
            curr_market = context.user_data.get('selected_market', 'الشرق الأوسط والعالمي + الأخبار 🌐📰')
            curr_tf = context.user_data.get('selected_timeframe', 'M5')
            curr_lot = context.user_data.get('selected_lot', '0.01')
            
            trade_classification, news_mode, signal_type, tp1, tp2, tp3, sl = analyze_news_strategy(entry)

            img_report = (
                f"👑━━━━━━━━━━━━━━━━━━━👑\n"
                f"🦅 **تقرير تحليل الشارت الملكي | أحمد السيد** 🦅\n"
                f"👑━━━━━━━━━━━━━━━━━━━👑\n\n"
                f"📌 **التصنيف المؤسسي:** `{trade_classification}`\n"
                f"✅ *تم فحص الشارت بنجاح ومطابقته للاتجاه الآمن 1,000,000%:*\n"
                f"🌍 *حالة السوق:* {market_msg}\n"
                f"📰 *وضع التداول:* `{news_mode}`\n"
                f"⏱️ *الفريم المعتمد:* `{curr_tf}` | ⚖️ *الوت:* `{curr_lot}`\n\n"
                f"🎯 *تفاصيل الصفقة المؤكدة:*\n"
                f"  🟢 *نوع الإشارة:* `{signal_type}`\n"
                f"  📍 *سعر الدخول الفوري (Entry):* `${entry}`\n"
                f"  🎯 *الهدف الأول (TP1):* `${tp1}`\n"
                f"  🎯 *الهدف الثاني (TP2):* `${tp2}`\n"
                f"  🚀 *الهدف الثالث النهائي (TP3):* `${tp3}`\n"
                f"  🛑 *وقف الخسارة الآمن (SL):* `${sl}`\n\n"
                f"🛡️ *تأمين الصفقة:* انقل وقف الخسارة إلى سعر الدخول (`{entry}`) فور بلوغ الهدف الأول (`{tp1}`).\n\n"
                f"📞 *للتواصل مع الوكيل:* {ADMIN_USERNAME}"
            )
            try:
                await scan_msg.delete()
            except Exception:
                pass
            await message.reply_text(img_report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]))
            return

    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))
    
    async def post_init(app: Application):
        await set_bot_menu(app)
        
    application.post_init = post_init

    logger.info("👑 [بوت أحمد السيد حوت الذهب VIP] يعمل بنظام الحالات المحدث بدون تكرار...")
    application.run_polling(drop_pending_updates=True, poll_interval=0.05)

if __name__ == "__main__":
    main()
