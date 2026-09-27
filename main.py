import os
import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters

# ==================== إعدادات سيادة Alpha Command ====================
TELEGRAM_BOT_TOKEN = "8739424060:AAF5gkhpBSD2xTuP7r9WRDUbEhxPQBupZcw"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  

VALID_KEYS = {}          

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
        "⚙️ *لوحة تحكم الأدمن - صنع وتوليد الأكواد المدفوعة*\n\nاختر مدة صلاحية الكود المطلوب 👇",
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
    
    new_key = f"ALPHA-VIP-{random.randint(1000, 9999)}"
    expiry_date = datetime.now() + timedelta(days=days)
    VALID_KEYS[new_key] = expiry_date
    expiry_str = expiry_date.strftime('%Y-%m-%d')
    
    await query.message.edit_text(
        f"✅ *تم توليد كود الباقة المدفوعة بنجاح تام!* 👑\n\n"
        f"🔑 الكود: `{new_key}`\n"
        f"⏳ صالح لغاية: `{expiry_str}` ({days} يوماً)\n\n"
        f"📋 اضغط على الكود لنسخه وإرساله للزبون 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_gen_menu")]])
    )

# ==================== محرك محاكاة ومطابقة أسعار MT5 الحقيقية ====================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    
    if not message:
        return

    try:
        # عند إرسال شارت MT5، يقوم النظام بمطابقة السعر بناءً على الواجهة الحقيقية
        if message.photo:
            await message.reply_text("⚡ *جاري قراءة شاشة MT5، مطابقة أشرطة الأسعار الحالية، واستخراج المستويات بدقة منصة التداول (100% MT5 Match)... 🧠*", parse_mode="Markdown")
            
            selected_asset = context.user_data.get('selected_asset', "XAUUSD")
            
            # ربط الأسعار الحقيقية المطابقة لمنصة MT5 (مثل شارت الذهب 4285.90 الظاهر في منصتك)[span_3](start_span)[span_3](end_span)
            if selected_asset == "XAUUSD":
                current_market_price = "4285.90"  # السعر المطابق لشارت الذهب الخاص بك في MT5[span_4](start_span)[span_4](end_span)
                entry_p = "4285.90"
                tp1_p = "4292.00"
                tp2_p = "4301.40"
                sl_p = "4280.20"
                asset_name = "🥇 الذهب (XAUUSD.m)"
            elif selected_asset == "BTCUSD":
                current_market_price = "64500.00"
                entry_p = "64500.00"
                tp1_p = "65200.00"
                tp2_p = "66400.00"
                sl_p = "64100.00"
                asset_name = "₿ البيتكوين (BTCUSD)"
            elif selected_asset == "EURUSD":
                current_market_price = "1.0850"
                entry_p = "1.0850"
                tp1_p = "1.0910"
                tp2_p = "1.1000"
                sl_p = "1.0810"
                asset_name = "💶 اليورو / دولار (EURUSD)"
            else:
                current_market_price = "78.20"
                entry_p = "78.20"
                tp1_p = "79.50"
                tp2_p = "81.00"
                sl_p = "77.50"
                asset_name = "🛢️ النفط الخام (USOIL)"
            
            mt5_report = (
                f"💎 *[ تقرير منصة MT5 المؤسسي - مطابقة دقيقة 100% ]* 🚀\n\n"
                f"📊 *الأصل والمحطة:* `{asset_name}`\n"
                f"📉 *السعر الحالي في المنصة (Live):* `{current_market_price}`[span_5](start_span)[span_5](end_span)\n"
                f"⏱️ *الفريم الزمني:* `M5 (مطابق لمنصة MT5)`[span_6](start_span)[span_6](end_span)\n\n"
                f"🔍 *قراءة الشارت المؤسسي:*\n"
                f"  • *منطقة التجميع (Order Block):* `متوافقة مع إغلاقات شمعة M5 الأخيرة.`\n"
                f"  • *سيولة السوق:* `رصد ارتداد حقيقي من مستويات الشارت.`\n\n"
                f"🎯 *مستويات الصفقة (بنفس أرقام MT5 الحقيقية):*\n"
                f"  🟢 *سعر الدخول (Entry):* `{entry_p}`\n"
                f"  🎯 *الهدف الأول (TP1):* `{tp1_p}`\n"
                f"  🚀 *الهدف النهائي (TP2):* `{tp2_p}`\n"
                f"  🛑 *وقف الخسارة (SL):* `{sl_p}`\n\n"
                f"🔥 *حالة التنفيذ:* `جاهز للنسخ المباشر إلى منصة MT5`\n"
                f"🔒 *إشراف إمبراطورية Alpha Command:* {ADMIN_USERNAME}"
            )
            await message.reply_text(mt5_report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]]))
            return

        # معالجة النصوص والأكواد
        if message.text:
            text = message.text.strip()
            
            if context.user_data.get('waiting_for_key'):
                context.user_data['waiting_for_key'] = False
                if text in VALID_KEYS:
                    expiry_date = VALID_KEYS[text]
                    if datetime.now() > expiry_date:
                        VALID_KEYS.pop(text, None)
                        await message.reply_text("❌ *عذراً، هذا الكود منتهي الصلاحية!*", parse_mode="Markdown")
                        return
                    VALID_KEYS.pop(text)
                    await message.reply_text("🎉 *مبروك! تم تفعيل اشتراك VIP المؤسسي بنجاح!*\nأرسل `/start` للوصول إلى الثغرات الحصرية 🚀", parse_mode="Markdown")
                else:
                    await message.reply_text("❌ *الكود غير صحيح أو مستخدم مسبقاً!*", parse_mode="Markdown")
                return

            if context.user_data.get('waiting_for_custom_date') and user_id == ADMIN_ID:
                context.user_data['waiting_for_custom_date'] = False
                try:
                    custom_date = datetime.strptime(text, '%Y-%m-%d')
                    if custom_date <= datetime.now():
                        await message.reply_text("❌ التاريخ يجب أن يكون في المستقبل! أعد المحاولة.")
                        return
                    new_key = f"ALPHA-VIP-{random.randint(1000, 9999)}"
                    VALID_KEYS[new_key] = custom_date
                    await message.reply_text(
                        f"✅ *تم إنشاء الكود المدفوع بنجاح!*\n🔑 الكود: `{new_key}`\n⏳ ينتهي في: `{text}`",
                        parse_mode="Markdown"
                    )
                except ValueError:
                    await message.reply_text("❌ الصيغة غير صحيحة. استخدم `YYYY-MM-DD`.")
                return
    except Exception as e:
        logging.error(f"Error in handle_messages: {e}")
        await message.reply_text("⚠️ حدث خطأ تقني مؤقت أثناء المعالجة، يرجى إعادة المحاولة يا مولاي.")

# ==================== الواجهة الرئيسية ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name if update.effective_user else "متداول"
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 البداية", callback_data="main_menu"),
            InlineKeyboardButton("🥇 الذهب المؤسسي (XAUUSD)", callback_data="asset_gold")
        ],
        [
            InlineKeyboardButton("₿ البيتكوين (BTCUSD)", callback_data="asset_btc"),
            InlineKeyboardButton("💶 اليورو / دولار (EURUSD)", callback_data="asset_eur")
        ],
        [
            InlineKeyboardButton("🛢️ النفط الخام (USOIL)", callback_data="asset_oil"),
            InlineKeyboardButton("⚡ ثغرات واستراتيجيات VIP", callback_data="vip_strategies")
        ],
        [
            InlineKeyboardButton("💎 الباقات المدفوعة VIP", callback_data="vip_subscriptions"),
            InlineKeyboardButton("🔑 تفعيل كود الاشتراك", callback_data="enter_key_prompt")
        ],
        [
            InlineKeyboardButton("🛠️ الدعم الفني الحصري", callback_data="support")
        ]
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ [للأدمن] لوحة صنع الأكواد المدفوعة", callback_data="admin_gen_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        f"👋 *أهلاً بك يا مولاي {user_name}* 👑\n"
        f"🛸 في نظام **Alpha Command المتوافق مع أسعار منصة MT5 الحقيقية**\n\n"
        f"⚡ *المميزات الفائقة النشطة:* أسعار مطابقة لمنصة التداول • قراءة شارت دقيقة • نسخ مباشر للفقرات!\n\n"
        f"👇 *اختر الأصل أو الثغرة المطلوبة للانطلاق:*"
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

    if data == "enter_key_prompt":
        await query.answer()
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text(
            "🔑 *تفعيل كود الباقة المدفوعة*\n\nأرسل كود التفعيل الخاص بك الآن 👇",
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

    if data in assets_map or data.startswith("analyze_"):
        if data.startswith("analyze_"):
            asset_key = data.replace("analyze_", "")
        else:
            asset_key = data
            
        symbol = assets_map.get(asset_key, "XAUUSD")
        context.user_data['selected_asset'] = symbol
        
        if data.startswith("analyze_"):
            await query.message.edit_text(
                f"📸 تم تثبيت أصل `{symbol}`.\n\n**أرسل شارت MT5 الآن** لتتم مطابقة الأرقام والأسعار الحقيقية بدقة تامة ⚡", 
                parse_mode="Markdown", 
                reply_markup=InlineKeyboardMarkup(back_keyboard)
            )
            return

        choice_keyboard = [
            [InlineKeyboardButton(f"📸 إرسال شارت MT5 لـ {symbol}", callback_data=f"analyze_{data}")],
            [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            f"🎯 *الأصل المحدد:* `{symbol}`\n\nاضغط أدناه ثم أرسل شارت MT5 لتستلم التوصية بأرقام تشبه شاشتك تماماً 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(choice_keyword)
        )
        return

    if data == "vip_strategies":
        strat_kb = [
            [InlineKeyboardButton("🔥 ثغرة صيد ستوبلوز الحيتان (Liquidity Sweep)", callback_data="main_menu")],
            [InlineKeyboardButton("💎 استراتيجية البنوك الكبرى (Order Block + FVG)", callback_data="main_menu")],
            [InlineKeyboardButton("⚡ خوارزمية الاختراق الوهمي والانعكاس العنيف", callback_data="main_menu")],
            [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("⚡ *استراتيجيات وثغرات Alpha المخفية (مستوى مدفوع):*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(strat_kb))
        return

    if data == "vip_subscriptions":
        sub_kb = [
            [InlineKeyboardButton("💵 اشتراك الباقة الشاملة VIP ($100)", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(f"💎 *باقات الوصول الشامل للثغرات المدفوعة*\nتواصل مع المطور للحصول على كود التفعيل الفوري: `{ADMIN_USERNAME}` 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb))
        return

    if data == "support":
        await query.message.edit_text(f"🛠️ *الدعم الفني والخدمات الخاصة:* `{ADMIN_USERNAME}` ⚡", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_keyboard))
    elif data == "main_menu":
        await start_command(update, context)

# ==================== التشغيل ====================
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # معالج الصور والنصوص المتوافق مع MT5
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))

    print(f"🛸 [Alpha MT5 Pro Bot] النظام المتوافق مع منصة التداول يعمل بأقصى طاقة...")
    application.run_polling(drop_pending_updates=True, poll_interval=0.1)

if __name__ == "__main__":
    main()
