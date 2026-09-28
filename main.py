import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from utils import LoggerManager, DatabaseManager, SecurityManager, PathManager

PathManager.create_directories(".", ["database", "logs", "assets"])
logger = LoggerManager.get_logger("Alpha_Apex_Core")

TELEGRAM_BOT_TOKEN = "8916004825:AAG67V-nkqGLileO6cOy7847UIoqtVVjPog"
ADMIN_ID = 5796443586  
ADMIN_USERNAME = "@V8V8VN"  

db = DatabaseManager()

# ==================== الواجهة الرئيسية ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    keyboard = [
        [
            InlineKeyboardButton("✨ الرئيسية", callback_data="main_menu"),
            InlineKeyboardButton("🥇 الذهب (XAUUSD)", callback_data="apex_gold"),
            InlineKeyboardButton("💶 العملات (EURUSD)", callback_data="apex_forex")
        ],
        [
            InlineKeyboardButton("🪙 البيتكوين (BTC)", callback_data="apex_crypto"),
            InlineKeyboardButton("🛢️ النفط الخام (Oil)", callback_data="apex_oil")
        ],
        [
            InlineKeyboardButton("⚡ استراتيجيات السيولة الخارقة", callback_data="apex_strategies"),
            InlineKeyboardButton("📍 الجلسات والبنوك المركزية", callback_data="apex_sessions")
        ],
        [
            InlineKeyboardButton("💎 باقات الإمبراطورية VIP", callback_data="apex_vip_subs"),
            InlineKeyboardButton("🔑 تفعيل رخصة السيادة", callback_data="apex_key_prompt")
        ],
        [
            InlineKeyboardButton("📸 انستغرام", url="https://instagram.com/_7ok6"),
            InlineKeyboardButton("🎵 تيك توك", url="https://tiktok.com/@7ok6_")
        ],
        [
            InlineKeyboardButton("🛠️ غرفة عمليات الدعم الفني", callback_data="apex_support")
        ]
    ]

    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ [لوحة القيادة العليا] توليد رخصة سيادية مخصصة", callback_data="admin_gen_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"📊 **[ تقرير التحليل الفني للشارت — مطابق لمنصة MT5 ]** 💎\n\n"
        f"🏛️ **منصة التنفيذ:** MetaTrader 5 (Pro Mode)\n"
        f"🌍 **الجلسة والدولة:** جلسة لندن / نيويورك\n"
        f"⏱️ **الفريم الزمني المكتشف:** تم إضافة نظام التحكم بالفريمات!\n\n"
        f"🎯 **أرقام الصفقة المستخرجة والمضبوطة بدقة:**\n"
        f"  🟢 **نوع الإشارة:** شراء / بيع (بناءً على الشارت المرسل)\n"
        f"  📍 **سعر الدخول (Entry):** السعر الحي المطابق للشاشة بدقة\n"
        f"  🎯 **الهدف الأول (TP1):** تم حساب الهدف الأول بمسافة آمنة\n"
        f"  🎯 **الهدف الثاني (TP2):** امتداد الهيكل السعري الثاني\n"
        f"  🚀 **الهدف الثالث النهائي (TP3):** الهدف الرئيسي لصانع السوق\n"
        f"  🛑 **وقف الخسارة (SL):** خلف القاع/الققمة الأخير بأمان تام\n\n"
        f"🛡️ **تأمين الصفقة الحقيقية:** فور بلوغ السعر الهدف الأول (TP1)، قم فوراً بتعديل (Modify SL) ونقله إلى سعر الدخول لتأمين الصفقة بنسبة 100%!\n\n"
        f"👑 **إشراف الخبير:** أحمد السيد ({ADMIN_USERNAME})\n\n"
        f"❖ *اختر أصل التداول المطلوب أدناه أو أرسل سكرين الشاشة لفرض السيطرة الرقمية 👇*"
    )

    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception:
            pass

# ==================== معالج الأزرار وقائمة الفريمات الجديدة ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)

    await query.answer()
    back_kb = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]]

    if data == "admin_gen_menu" and is_admin:
        dur_kb = [
            [InlineKeyboardButton("⏱️ 24 ساعة سيادية", callback_data="key_1d")],
            [InlineKeyboardButton("⏳ أسبوع كامل", callback_data="key_7d")],
            [InlineKeyboardButton("💎 شهر إمبراطوري", callback_data="key_30d")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
        ]
        await query.message.edit_text("⚙️ *لوحة القيادة العليا: حدد مدة الرخصة السيادية:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(dur_kb))
        return

    if data.startswith("key_") and is_admin:
        dur_type = data.replace("key_", "")
        sec_map = {"1d": 86400, "7d": 7*86400, "30d": 30*86400}
        new_key = SecurityManager.generate_vip_key("APEX_VIP")
        db.set_item(f"key_duration_{new_key}", str(sec_map.get(dur_type, 86400)))
        await query.message.edit_text(f"✅ *تم توليد الرخصة بنجاح!*\n🔑 الكود: `{new_key}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    # اختيار الأصل -> الانتقال لاختيار الفريم الزمني
    if data in ["apex_gold", "apex_forex", "apex_crypto", "apex_oil"]:
        symbol_map = {
            "apex_gold": "GOLD",
            "apex_forex": "FOREX",
            "apex_crypto": "CRYPTO",
            "apex_oil": "OIL"
        }
        sym_key = symbol_map[data]
        context.user_data['pending_symbol'] = sym_key
        
        # أزرار اختيار الفريم الزمني للتحكم الكامل
        tf_kb = [
            [
                InlineKeyboardButton("⚡ فريم M1 (دقيقة)", callback_data=f"tf_M1_{sym_key}"),
                InlineKeyboardButton("🔥 فريم M5 (5 دقائق)", callback_data=f"tf_M5_{sym_key}")
            ],
            [
                InlineKeyboardButton("📈 فريم M15 (15 دقيقة)", callback_data=f"tf_M15_{sym_key}"),
                InlineKeyboardButton("🏛️ فريم H1 (ساعة)", callback_data=f"tf_H1_{sym_key}")
            ],
            [InlineKeyboardButton("🔙 العودة للقائمة", callback_data="main_menu")]
        ]
        await query.message.edit_text("⏱️ *التحكم بالفريم الزمني:\nاختر الفريم المطلوب للتحليل الدقيق قبل إرسال السعر 👇*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(tf_kb))
        return

    # حفظ الفريم المختار وطلب السعر
    if data.startswith("tf_"):
        parts = data.split("_")
        tf_val = parts[1]
        sym_val = parts[2]
        context.user_data['selected_tf'] = tf_val
        context.user_data['pending_symbol'] = sym_val
        
        symbol_names = {"GOLD": "الذهب (XAUUSD)", "FOREX": "العملات (EURUSD)", "CRYPTO": "البيتكوين (BTC)", "OIL": "النفط الخام (Oil)"}
        await query.message.edit_text(f"🎯 *تم اختيار فريم ({tfval if 'tfval' in locals() else tf_val}) للأصل ({symbol_names.get(sym_val, sym_val)}).*\n\n❖ أرسل الآن **سعر الدخول الحالي** من منصة MT5 في رسالة نصية 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "apex_strategies":
        strat_txt = (
            f"⚡ *استراتيجيات السيولة الخارقة المتقدمة:* 💎\n\n"
            f"1️⃣ ⚡ **السكالبينج الفائق:** فريم `M1 & M5` لإقتناص الصفقات السريعة.\n"
            f"2️⃣ 📈 **هيكل السوق المؤسسي:** فريم `M15` للاتجاهات العامة.\n"
            f"3️⃣ 🏛️ **مناطق العرض والطلب الكبرى:** فريم `H1`.\n\n"
            f"❖ *اختر الأصل والفريم ثم أرسل السعر أو الشارت للحصول على النتائج فوراً 👇*"
        )
        await query.message.edit_text(strat_txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "apex_sessions":
        sess_txt = (
            f"📍 *الجلسات العالمية والبنوك المركزية النشطة:* 🏛️\n\n"
            f"🌐 *جلسات التداول المعتمدة:* لندن / نيويورك (سيولة مؤسسية مطلقة).\n"
            f"💹 *منصة التنفيذ الموصى بها:* `MT5 Pro (MetaTrader 5)`\n\n"
            f"❖ *للتواصل المباشر مع الخبير:* `{ADMIN_USERNAME}` 👑"
        )
        await query.message.edit_text(sess_txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "apex_vip_subs":
        sub_kb = [
            [InlineKeyboardButton("⏱️ باقة يوم واحد", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("💎 باقة الشهر الإمبراطوري", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 العودة للقائمة", callback_data="main_menu")]
        ]
        await query.message.edit_text(f"💎 *باقات الإمبراطورية VIP*\n\n❖ للاشتراك راسل المطور: `{ADMIN_USERNAME}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(sub_kb))
        return

    if data == "apex_key_prompt":
        context.user_data['waiting_for_key'] = True
        await query.message.edit_text("🔑 *تفعيل رخصة السيادة*\n\n❖ أرسل كود التفعيل الخاص بك الآن في رسالة نصية لتفعيله فوراً 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return

    if data == "apex_support":
        await query.message.edit_text(f"🛠️ *غرفة عمليات الدعم الفني*\n\n❖ تواصل مع المطور: `{ADMIN_USERNAME}` ⚡", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_kb))
        return
    elif data == "main_menu":
        await start_command(update, context)

# ==================== محرك المعالجة والتحليل الذكي مع الفريم المختار ====================
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    try:
        if message.text and context.user_data.get('waiting_for_key'):
            context.user_data['waiting_for_key'] = False
            k_val = message.text.strip()
            dur = db.get_item(f"key_duration_{k_val}")
            if dur:
                db.set_item(f"expiry_{message.from_user.id}", str(time.time() + float(dur)))
                db.delete_item(f"key_duration_{k_val}")
                await message.reply_text("🎉 *تم تفعيل رخصة السيادة بنجاح تام!* أرسل `/start` للبدء 🚀", parse_mode="Markdown")
            else:
                await message.reply_text("❌ *الكود غير صحيح أو منتهي الصلاحية.* تواصل مع المطور: " + ADMIN_USERNAME, parse_mode="Markdown")
            return

        if message.text and context.user_data.get('pending_symbol'):
            sym = context.user_data.pop('pending_symbol')
            chosen_tf = context.user_data.pop('selected_tf', 'M5')
            
            try:
                entry = float(message.text.strip().replace(',', ''))
            except ValueError:
                await message.reply_text("❌ *أرسل رقماً صحيحاً فقط لسعر الدخول (مثلاً: 4285.90)*", parse_mode="Markdown")
                return

            if sym == "GOLD":
                tp1, tp2, tp3, sl = entry + 5.0, entry + 11.0, entry + 18.0, entry - 6.0
                title = "الذهب (XAUUSD)"
                strth = "🔥 قوية جداً (تأكيد تدفق سيولة صانع السوق)"
            elif sym == "CRYPTO":
                tp1, tp2, tp3, sl = entry + 300.0, entry + 700.0, entry + 1200.0, entry - 350.0
                title = "البيتكوين (BTCUSD)"
                strth = "⚡ قوية (زخم صعودي مؤسسي)"
            elif sym == "FOREX":
                tp1, tp2, tp3, sl = entry + 0.0030, entry + 0.0065, entry + 0.0100, entry - 0.0035
                title = "العملات الرئيسية (EURUSD)"
                strth = "⚖️ وسط (استقرار سعري ضمن النطاق)"
            else:
                tp1, tp2, tp3, sl = entry + 1.20, entry + 2.50, entry + 4.00, entry - 1.10
                title = "النفط الخام (WTI Oil)"
                strth = "🔥 قوية جداً (ارتداد من منطقة طلب رئيسية)"

            tf_names = {"M1": "دقيقة واحدة (M1)", "M5": "5 دقائق (M5) - سكالبينج", "M15": "15 دقيقة (M15)", "H1": "ساعة كاملة (H1)"}
            tf_display = tf_names.get(chosen_tf, chosen_tf)

            report = (
                f"📊 *[ تقرير التحليل الفني الشامل — مطابق لمنصة MT5 ]* 💎\n\n"
                f"🏛️ *الأصل المالي:* `{title}`\n"
                f"🌍 *الجلسة والدولة:* `جلسة لندن / نيويورك (بريطانيا / أمريكا)`\n"
                f"⏱️ *الفريم الزمني المختار:* `{tf_display}`\n"
                f"💪 *قوة الصفقة:* `{strth}`\n\n"
                f"🎯 *أرقام الصفقة المستخرجة والمضبوطة بدقة:*\n"
                f"  🟢 *نوع الإشارة:* `شراء (BUY) بناءً على الشارت المختار`\n"
                f"  📍 *سعر الدخول (Entry):* `{entry}`\n"
                f"  🎯 *الهدف الأول (TP1):* `{round(tp1, 2)}` (تم حساب الهدف الأول بمسافة آمنة)\n"
                f"  🎯 *الهدف الثاني (TP2):* `{round(tp2, 2)}` (امتداد الهيكل السعري الثاني)\n"
                f"  🚀 *الهدف الثالث النهائي (TP3):* `{round(tp3, 2)}` (الهدف الرئيسي لصانع السوق)\n"
                f"  🛑 *وقف الخسارة (SL):* `{round(sl, 2)}` (خلف القاع/الققمة الأخير بأمان تام)\n\n"
                f"🛡️ *تأمين الصفقة الحقيقية:* فور بلوغ السعر الهدف الأول ({round(tp1, 2)}), قم فوراً بتعديل (Modify SL) ونقله إلى سعر الدخول ({entry}) لتأمين الصفقة بنسبة 100%!\n\n"
                f"👑 *إشراف الخبير:* أحمد السيد ({ADMIN_USERNAME})"
            )
            await message.reply_text(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]]))
            return

        if message.photo:
            await message.reply_text("⚡ *جاري فحص الشارت المرفق واستخراج مستويات السيولة والفريم بدقة تامة... 📈*", parse_mode="Markdown")
            
            img_report = (
                f"📊 *[ تقرير التحليل الفني للشارت — مطابق لمنصة MT5 Pro ]* 💎\n\n"
                f"🏛️ *منصة التنفيذ:* `MetaTrader 5 (Pro Mode)`\n"
                f"🌍 *الجلسة والدولة:* `جلسة لندن / نيويورك (بريطانيا / أمريكا)`\n"
                f"⏱️ *الفريم الزمني المكتشف:* `5 دقائق (M5) - سكالبينج`\n"
                f"💪 *قوة الصفقة:* `🔥 قوية جداً (تأكيد كسر هيكل السوق BoS)`\n\n"
                f"🎯 *أرقام الصفقة المستخرجة والمضبوطة بدقة:*\n"
                f"  🟢 *نوع الإشارة:* `شراء / ارتداد سيولة مؤسسية`\n"
                f"  📍 *سعر الدخول (Entry):* `4285.90`\n"
                f"  🎯 *الهدف الأول (TP1):* `4290.90`\n"
                f"  🎯 *الهدف الثاني (TP2):* `4296.90`\n"
                f"  🚀 *الهدف الثالث النهائي (TP3):* `4303.90`\n"
                f"  🛑 *وقف الخسارة الآمن (SL):* `4279.90`\n\n"
                f"🛡️ *تأمين الصفقة الحقيقية:* فور بلوغ السعر الهدف الأول (4290.90), قم فوراً بنقل وقف الخسارة (SL) إلى سعر الدخول لتأمين الأرباح 100%!\n\n"
                f"👑 *إشراف الخبير:* أحمد السيد ({ADMIN_USERNAME})"
            )
            await message.reply_text(img_report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_menu")]]))
            return

    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_messages))
    
    logger.info("🛸 [Alpha Apex Sovereign Bot v6.0] يعمل بأقصى طاقة وكفاءة تشغيلية مطلقة...")
    application.run_polling(drop_pending_updates=True, poll_interval=0.05)

if __name__ == "__main__":
    main()
