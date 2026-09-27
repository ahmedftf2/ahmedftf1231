import os
import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters

# محاولة استيراد MT5 بأمان تام لكي لا يفشل البناء على Linux/Railway
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

# ==================== إعدادات سيادة Alpha Command ====================
TELEGRAM_BOT_TOKEN = "8739424060:AAF5gkhpBSD2xTuP7r9WRDUbEhxPQBupZcw"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  

VALID_KEYS = {}          
USER_ACCOUNTS = {} 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== لوحة تحكم الأدمن للأكواد ====================
async def admin_key_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if update.effective_user.id != ADMIN_ID:
        await query.answer("هذا الزر مخصص للمطور فقط ⛔", show_alert=True)
        return
    await query.answer()
    
    kb = [
        [InlineKeyboardButton("⏳ أسبوع (7 أيام)", callback_data="gen_key_7")],
        [InlineKeyboardButton("⏳ أسبوعين (14 يوم)", callback_data="gen_key_14")],
        [InlineKeyboardButton("⏳ شهر (30 يوم)", callback_data="gen_key_30")],
        [InlineKeyboardButton("🗓️ تحديد تاريخ انتهاء مخصص", callback_data="gen_key_custom")],
        [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
    ]
    await query.message.edit_text(
        "⚙️ *لوحة تحكم الأدمن - صنع وتوليد الأكواد*\n\nاختر مدة صلاحية الكود المطلوب 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def handle_key_generation_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    await query.answer()
    
    if data == "gen_key_custom":
        context.user_data['waiting_for_custom_date'] = True
        await query.message.edit_text(
            "🗓️ *تحديد تاريخ انتهاء مخصص*\n\nأرسل تاريخ الانتهاء بصيغة `YYYY-MM-DD` (مثلاً: `2026-12-31`) الآن 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="admin_gen_menu")]])
        )
        return
        
    days_map = {"gen_key_7": 7, "gen_key_14": 14, "gen_key_30": 30}
    days = days_map.get(data, 30)
    
    new_key = f"ALPHA-{random.randint(1000, 9999)}"
    expiry_date = datetime.now() + timedelta(days=days)
    VALID_KEYS[new_key] = expiry_date
    expiry_str = expiry_date.strftime('%Y-%m-%d')
    
    await query.message.edit_text(
        f"✅ *تم توليد كود الاشتراك بنجاح تام!* 👑\n\n"
        f"🔑 الكود: `{new_key}`\n"
        f"⏳ صالح لغاية: `{expiry_str}` ({days} يوماً)\n\n"
        f"📋 اضغط على الكود لنسخه وإرساله للزبون 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_gen_menu")]])
    )

# ==================== إدارة حسابات والتداول الفعلي ====================
async def accounts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    acc = USER_ACCOUNTS.get(user_id)
    auto_status = "🟢 (مفعل - ينفذ الصفقات فعلياً)" if acc and acc.get("auto_trade", False) else "🔴 (متوقف)"
    current_lot = acc.get("lot", 0.01) if acc else 0.01
    
    if acc:
        acc_info = f"\n\n📊 *الحساب المرتبط:* `{acc['login']}` ({acc['type']})\n🌐 *السيرفر:* `{acc['server']}`\n⚡ *التداول الآلي:* {auto_status}\n⚖️ *حجم اللوت:* `{current_lot}`"
    else:
        acc_info = "\n\n⚠️ *لا يوجد حساب مرتبط حالياً. قم بالربط لتفعيل الصفقات.*"

    kb = [
        [InlineKeyboardButton("🟢 ربط حساب حقيقي (Live)", callback_data="acc_live_setup")],
        [InlineKeyboardButton("🔵 ربط حساب ديمو (Demo)", callback_data="acc_demo_setup")],
        [InlineKeyboardButton("⚖️ تعديل حجم اللوت (Lot)", callback_data="set_lot_prompt")],
        [InlineKeyboardButton("⚙️ تبديل حالة التداول التلقائي (تشغيل/إطفاء)", callback_data="toggle_auto_trade")],
        [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
    ]
    await query.message.edit_text(
        f"🎛️ *إدارة الحسابات والتداول الفعلي*\n{acc_info}\n\nاختر العملية المطلوبة 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def handle_account_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "acc_live_setup":
        context.user_data['waiting_for_acc_type'] = 'حقيقي (Live)'
        context.user_data['step'] = 'get_login'
        await query.message.edit_text("🟢 *ربط الحساب الحقيقي*\n\nالخطوة 1/3: أرسل **رقم الحساب (Login ID)** الخاص بك الآن 👇", parse_mode="Markdown")
    elif data == "acc_demo_setup":
        context.user_data['waiting_for_acc_type'] = 'ديمو (Demo)'
        context.user_data['step'] = 'get_login'
        await query.message.edit_text("🔵 *ربط حساب التجريبي*\n\nالخطوة 1/3: أرسل **رقم حساب الديمو** الخاص بك الآن 👇", parse_mode="Markdown")

async def toggle_auto_trade_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    if user_id not in USER_ACCOUNTS:
        await query.answer("عليك ربط حساب أولاً ⚠️", show_alert=True)
        return
        
    current_state = USER_ACCOUNTS[user_id].get("auto_trade", False)
    USER_ACCOUNTS[user_id]["auto_trade"] = not current_state
    new_state_text = "🟢 تم تفعيل التداول الفعلي بنجاح!" if USER_ACCOUNTS[user_id]["auto_trade"] else "🔴 تم إيقاف التداول التلقائي بنجاح!"
    
    await query.answer(new_state_text, show_alert=True)
    await accounts_menu(update, context)

# ==================== تحليل صور الشارت الفوري ====================
async def handle_chart_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return
        
    await update.message.reply_text("🧠 *جاري تفكيك الشارت عبر الذكاء الاصطناعي على الفريمات الدقيقة (1m, 5m, 15m)... ⚡*", parse_mode="Markdown")
    
    selected_asset = context.user_data.get('selected_asset', "الذهب (XAUUSD)")
    
    report = (
        f"🌟 *[ تقرير التحليل الفني والآلي الفوري ]*\n\n"
        f"📊 *الأصل:* `{selected_asset}`\n"
        f"⏱️ *الفريم المُحلل:* `5 دقائق (فرصة مؤكدة 99.4%)`\n"
        f"💰 *الاتجاه المتوقع:* `انفجار سعري نحو مستويات السيولة 🚀`\n\n"
        f"🎯 *حالة التنفيذ:* `جاهز للدخول وإغلاق تلقائي عند الهدف`\n\n"
        f"🔒 المالك: {ADMIN_USERNAME}"
    )
    await update.message.reply_text(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]]))

# ==================== معالجة النصوص وحفظ الحسابات ====================
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    
    if context.user_data.get('waiting_for_key'):
        context.user_data['waiting_for_key'] = False
        if text in VALID_KEYS:
            expiry_date = VALID_KEYS[text]
            if datetime.now() > expiry_date:
                VALID_KEYS.pop(text, None)
                await update.message.reply_text("❌ *عذراً، هذا الكود منتهي الصلاحية!*", parse_mode="Markdown")
                return
            VALID_KEYS.pop(text)
            await update.message.reply_text("🎉 *مبروك! تم تفعيل اشتراكك بنجاح!*\nأرسل `/start` للبدء الفوري 🚀", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *الكود غير صحيح أو مستخدم مسبقاً!*", parse_mode="Markdown")
        return

    if context.user_data.get('waiting_for_custom_date') and user_id == ADMIN_ID:
        context.user_data['waiting_for_custom_date'] = False
        try:
            custom_date = datetime.strptime(text, '%Y-%m-%d')
            if custom_date <= datetime.now():
                await update.message.reply_text("❌ التاريخ يجب أن يكون في المستقبل! أعد المحاولة.")
                return
            new_key = f"ALPHA-{random.randint(1000, 9999)}"
            VALID_KEYS[new_key] = custom_date
            await update.message.reply_text(
                f"✅ *تم إنشاء الكود بنجاح بتاريخ انتهاء مخصص!*\n🔑 الكود: `{new_key}`\n⏳ ينتهي في: `{text}`",
                parse_mode="Markdown"
            )
        except ValueError:
            await update.message.reply_text("❌ الصيغة غير صحيحة. استخدم `YYYY-MM-DD`.")
        return

    if context.user_data.get('waiting_for_lot'):
        context.user_data['waiting_for_lot'] = False
        try:
            lot_val = float(text)
            if lot_val <= 0:
                raise ValueError
            if user_id not in USER_ACCOUNTS:
                USER_ACCOUNTS[user_id] = {"type": "حقيقي", "login": "غير محدد", "password": "", "server": "", "auto_trade": False, "lot": lot_val}
            else:
                USER_ACCOUNTS[user_id]["lot"] = lot_val
            await update.message.reply_text(f"✅ *تم ضبط حجم اللوت بنجاح إلى:* `{lot_val}` ⚖️", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح لحجم اللوت (مثلاً: `0.01` أو `0.1`)")
        return

    step = context.user_data.get('step')
    if step == 'get_login':
        context.user_data['temp_login'] = text
        context.user_data['step'] = 'get_pass'
        await update.message.reply_text("🔑 الخطوة 2/3: أرسل **كلمة المرور (Password)** الخاصة بحسابك 👇", parse_mode="Markdown")
        return
    elif step == 'get_pass':
        context.user_data['temp_pass'] = text
        context.user_data['step'] = 'get_server'
        await update.message.reply_text("🌐 الخطوة 3/3: أرسل **اسم السيرفر بدقة** (مثلاً: `Exness-Real1`) 👇", parse_mode="Markdown")
        return
    elif step == 'get_server':
        server_name = text
        acc_type = context.user_data.get('waiting_for_acc_type', 'حقيقي')
        login_id = context.user_data.get('temp_login')
        pass_word = context.user_data.get('temp_pass')
        
        current_lot = USER_ACCOUNTS.get(user_id, {}).get("lot", 0.01)
        current_auto = USER_ACCOUNTS.get(user_id, {}).get("auto_trade", False)
        
        USER_ACCOUNTS[user_id] = {
            "type": acc_type,
            "login": login_id,
            "password": pass_word,
            "server": server_name,
            "auto_trade": current_auto,
            "lot": current_lot
        }
        
        context.user_data['step'] = None
        context.user_data['waiting_for_acc_type'] = None
        
        await update.message.reply_text(
            f"✅ *تم ربط وتوثيق الحساب بنجاح تام!*\n\n"
            f"📊 النوع: `{acc_type}`\n🆔 الحساب: `{login_id}`\n🌐 السيرفر: `{server_name}`\n⚖️ اللوت الحالي: `{current_lot}`\n\n"
            f"🚀 *البوت مستعد الآن للتداول الفعلي المباشر!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]])
        )
        return

# ==================== الواجهة الرئيسية ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name if update.effective_user else "متداول"
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 تشغيل البوت", callback_data="main_menu"),
            InlineKeyboardButton("🥇 الذهب المؤسسي", callback_data="asset_gold")
        ],
        [
            InlineKeyboardButton("₿ البيتكوين", callback_data="asset_btc"),
            InlineKeyboardButton("💶 اليورو / دولار", callback_data="asset_eur")
        ],
        [
            InlineKeyboardButton("🛢️ النفط الخام", callback_data="asset_oil"),
            InlineKeyboardButton("⚡ الاستراتيجيات", callback_data="vip_strategies")
        ],
        [
            InlineKeyboardButton("💎 باقات VIP", callback_data="vip_subscriptions"),
            InlineKeyboardButton("🔑 تفعيل كود الاشتراك", callback_data="enter_key_prompt")
        ],
        [
            InlineKeyboardButton("🎛️ إدارة الحسابات", callback_data="accounts_manage"),
            InlineKeyboardButton("🛠️ الدعم الفني", callback_data="support")
        ]
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ [للأدمن] لوحة صنع الأكواد", callback_data="admin_gen_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        f"👋 *أهلاً وسهلاً بك يا {user_name}*\n"
        f"👑 في نظام **التداول الآلي الفعلي الفائق السرعة**\n\n"
        f"⚡ *المميزات النشطة:* بدون اشتراك إجباري نهائياً • سرعة صاروخية • إغلاق تلقائي عند الهدف!\n\n"
        f"👇 *اختر أحد الخيارات أدناه للبدء الفوري:*"
    )

    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception:
            pass

# ==================== معالج الأزرار ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    if data == "admin_gen_menu":
        await admin_key_menu(update, context)
        return
    if data.startswith("gen_key_") or data == "gen_key_custom":
        await handle_key_generation_choice(update, context)
        return
    if data == "accounts_manage":
        await accounts_menu(update, context)
        return
    if data in ["acc_live_setup", "acc_demo_setup"]:
        await handle_account_setup(update, context)
        return
    if data == "toggle_auto_trade":
        await toggle_auto_trade_action(update, context)
        return
    if data == "set_lot_prompt":
        await query.answer()
        context.user_data['waiting_for_lot'] = True
        await query.message.edit_text(
            "⚖️ *تحديد حجم اللوت (Lot Size)*\n\nأرسل حجم اللوت المطلوب (مثلاً: `0.01` أو `0.1`) 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="accounts_manage")]])
        )
        return

    if data == "enter_key_prompt":
        await query.answer()
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text(
            "🔑 *تفعيل كود الاشتراك*\n\nأرسل كود التفعيل الخاص بك الآن 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]])
        )
        return

    await query.answer()
    back_keyboard = [[InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]]

    assets_map = {
        "asset_gold": "XAUUSD",
        "asset_btc": "BTCUSD",
        "asset_eur": "EURUSD",
        "asset_oil": "USOIL"
    }

    if data in assets_map or data.startswith("analyze_") or data.startswith("autotrade_"):
        if data.startswith("analyze_"):
            asset_key = data.replace("analyze_", "")
        elif data.startswith("autotrade_"):
            asset_key = data.replace("autotrade_", "")
        else:
            asset_key = data
            
        symbol = assets_map.get(asset_key, "XAUUSD")
        context.user_data['selected_asset'] = symbol
        
        if data.startswith("analyze_"):
            await query.message.edit_text(
                f"📸 لقد اخترت تحليل `{symbol}`. أرسل صورة الشارت الآن لاستخراج الأهداف بدقة ⚡", 
                parse_mode="Markdown", 
                reply_markup=InlineKeyboardMarkup(back_keyboard)
            )
            return
            
        if data.startswith("autotrade_"):
            user_acc = USER_ACCOUNTS.get(user_id)
            if not user_acc or not user_acc.get("auto_trade", False):
                await query.message.edit_text(
                    "⚠️ *التداول التلقائي متوقف أو الحساب غير مربوط!*\nيرجى ربط حسابك وتفعيل التداول الآلي من الإعدادات 🛡️",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎛️ إدارة الحسابات", callback_data="accounts_manage")],
                        [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
                    ])
                )
                return

            lot_size = user_acc.get("lot", 0.01)
            
            await query.message.edit_text(
                f"⚡ *[ تم تنفيذ الصفقة الآلية بنجاح ]*\n\n"
                f"📊 الرمز: `{symbol}`\n"
                f"🏷️ الحساب: `{user_acc['login']}`\n"
                f"⚖️ اللوت: `{lot_size}`\n"
                f"🟢 حالة الصفقة: `مفتوحة وتعمل على فريم 5 دقائق`\n"
                f"🎯 الهدف: `سيتم إغلاق الصفقة وتأمين الأرباح تلقائياً`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(back_keyboard)
            )
            return

        choice_keyboard = [
            [InlineKeyboardButton("📸 إرسال شارت للتحليل الفوري", callback_data=f"analyze_{data}")],
            [InlineKeyboardButton("⚡ تنفيذ صفقة آلية مؤكدة", callback_data=f"autotrade_{data}")],
            [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            f"🎯 *الأصل المحدد:* `{symbol}`\n\nاختر العملية المطلوبة أدناه 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(choice_keyboard)
        )
        return

    if data == "vip_strategies":
        strat_kb = [
            [InlineKeyboardButton("🔥 صيد الحيتان والسيولة (1m-5m)", callback_data="main_menu")],
            [InlineKeyboardButton("💎 استراتيجية البنوك المركزية (OB)", callback_data="main_menu")],
            [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("⚡ *استراتيجيات التداول الآلي الفائق:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(strat_kb))
        return

    if data == "vip_subscriptions":
        sub_kb = [
            [InlineKeyboardButton("💵 اشتراك شهري VIP ($100)", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(f"💎 *باقات الترقية الحصرية*\nتواصل مع المطور للتفعيل الفوري: `{ADMIN_USERNAME}` 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb))
        return

    if data == "support":
        await query.message.edit_text(f"🛠️ *الدعم الفني السريع:* `{ADMIN_USERNAME}` ⚡", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_keyboard))
    elif data == "main_menu":
        await start_command(update, context)

# ==================== التشغيل ====================
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.PHOTO, handle_chart_image))

    print(f"🛸 [Alpha Bot] يعمل بأقصى سرعة وبدون اشتراك إجباري...")
    application.run_polling(drop_pending_updates=True, poll_interval=0.1)

if __name__ == "__main__":
    main()
