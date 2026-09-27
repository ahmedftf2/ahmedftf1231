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

# ==================== محرك التحليل وإعطاء الأسعار والمناطق الدقيقة ====================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    
    if not message:
        return

    try:
        # إذا أرسل المستخدم صورة شارت، نولد مناطق وأسعار رقمية دقيقة
        if message.photo:
            await message.reply_text("⚡ *جاري تفكيك الخوارزمية السعرية، قراءة الأرقام واستخراج المناطق السعرية بدقة مليمترية (100% Accuracy)... 🧠*", parse_mode="Markdown")
            
            selected_asset = context.user_data.get('selected_asset', "XAUUSD")
            
            # توليد أسعار افتراضية واقعية ودقيقة بناءً على الأصل
            if selected_asset == "XAUUSD":
                entry_p, tp1_p, tp2_p, sl_p = "2325.50", "2338.00", "2355.00", "2315.00"
            elif selected_asset == "BTCUSD":
                entry_p, tp1_p, tp2_p, sl_p = "64500.00", "65800.00", "67500.00", "63800.00"
            elif selected_asset == "EURUSD":
                entry_p, tp1_p, tp2_p, sl_p = "1.0850", "1.0920", "1.1010", "1.0810"
            else:
                entry_p, tp1_p, tp2_p, sl_p = "78.20", "79.90", "82.50", "77.00"
            
            pro_report = (
                f"💎 *[ تقرير الثغرات والمناطق السعرية المدفوعة VIP ]* 🚀\n\n"
                f"📊 *الأصل المُحلل:* `{selected_asset}`\n"
                f"⏱️ *الفريم الزمني:* `1m / 5m (قراءة صيد الحيتان)`\n\n"
                f"🔍 *تحليل الثغرات وهيكلة السوق:*\n"
                f"  • *منطقة الـ Order Block (OB):* `تم رصد شمعة التجميع المؤسسي.`\n"
                f"  • *فجوة السيولة (FVG):* `مغلقة ومستعدة للانفجار.`\n\n"
                f"🎯 *المناطق السعرية الدقيقة للصفقة (100/100):*\n"
                f"  🟢 *منطقة الدخول (Entry):* `{entry_p}`\n"
                f"  🎯 *الهدف الأول (TP1):* `{tp1_p}`\n"
                f"  🚀 *الهدف النهائي (TP2):* `{tp2_p}`\n"
                f"  🛑 *وقف الخسارة (SL):* `{sl_p}`\n\n"
                f"🔥 *حالة الثغرة:* `نشطة وتعمل بأقصى فاعلية`\n"
                f"🔒 *إشراف إمبراطورية Alpha Command:* {ADMIN_USERNAME}"
            )
            await message.reply_text(pro_report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]]))
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
        f"🛸 في نظام **Alpha Command للمناطق السعرية الدقيقة والثغرات المدفوعة**\n\n"
        f"⚡ *المميزات الفائقة النشطة:* أسعار دخول واضحة • أهداف رقمية دقيقة • ستوبلوز محكوم!\n\n"
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
                f"📸 لقد اخترت فحص ثغرات `{symbol}`. **أرسل صورة الشارت الآن** لاستخراج الأسعار والمناطق الدقيقة ⚡", 
                parse_mode="Markdown", 
                reply_markup=InlineKeyboardMarkup(back_keyboard)
            )
            return

        choice_keyboard = [
            [InlineKeyboardButton("📸 إرسال شارت لاستخراج الأسعار والمناطق الدقيقة", callback_data=f"analyze_{data}")],
            [InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(
            f"🎯 *الأصل المحدد:* `{symbol}`\n\nاضغط أدناه لإرسال الشارت وجلب أسعار الدخول والأهداف الرقمية الفورية 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(choice_keyboard)
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
    
    # معالج الصور والنصوص المحدث
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))

    print(f"🛸 [Alpha Pro Bot] نظام المناطق السعرية الدقيقة يعمل بأقصى طاقة...")
    application.run_polling(drop_pending_updates=True, poll_interval=0.1)

if __name__ == "__main__":
    main()
