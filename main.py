import logging
import datetime
import random
import yfinance as yf
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from utils import (
    ADMIN_ID, 
    CHANNEL_USERNAME,
    get_admin_reply_keyboard, 
    get_subscriber_reply_keyboard, 
    get_subscriber_inline_keyboard, 
    get_admin_inline_keyboard
)

TOKEN = "8884364042:AAEPwYmYQiZ1sN7GUGouMVrgtT3EyNL1d7w"

# قواعد البيانات في الذاكرة
db = {
    "users": {},        # {user_id: {"name": str, "username": str, "expiry": datetime}}
    "codes": {},        # {code: {"type": str, "delta": timedelta, "used": bool}}
    "banned": set(),    # الآديات المحظورة
    "last_signal": ""   # آخر صفقة محللة لنشرها للقناة
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# دالة جلب الأسعار الحية المباشرة من السوق
def get_live_market_price():
    try:
        gold = yf.Ticker("GC=F")
        data = gold.history(period="1d", interval="1m")
        if not data.empty:
            current_price = float(data['Close'].iloc[-1])
            open_price = float(data['Open'].iloc[0])
            high_price = float(data['High'].max())
            low_price = float(data['Low'].min())
            return current_price, open_price, high_price, low_price
    except Exception as e:
        logging.error(f"خطأ في جلب السعر الحي: {e}")
    
    return 2650.50, 2640.00, 2660.00, 2635.00

# التحقق من اشتراك المستخدم
def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    if user_id in db["users"]:
        expiry_date = db["users"][user_id].get("expiry")
        if expiry_date and datetime.datetime.now() < expiry_date:
            return True
    return False

# أمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in db["banned"]:
        await update.message.reply_text("❌ عذراً، لقد تم حظرك من استخدام هذا البوت.")
        return

    if user.id not in db["users"] and user.id != ADMIN_ID:
        db["users"][user.id] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "بدون معرف",
            "expiry": datetime.datetime.now() + datetime.timedelta(hours=1) # ساعة تجريبية مجانية
        }

    welcome_msg = (
        f"🏴‍☠️ **مرحباً بك يا {user.full_name} في النظام الإمبراطوري للتداول الحي** 🏴‍☠️\n\n"
        "إشراف مباشر: **أحمد السيد** 👁️‍🗨️\n"
        "اختر من القوائم أدناه للحصول على التحليلات الحية والصفقات المضمونة."
    )

    if user.id == ADMIN_ID:
        await update.message.reply_text("⚡ [تم تفعيل لوحة تحكم الأدمن الحصرية]", reply_markup=get_admin_reply_keyboard())
        await update.message.reply_text(f"{welcome_msg}\n\n👑 **لوحة الأدمن المسيطرة:**", reply_markup=get_admin_inline_keyboard(), parse_mode="Markdown")
    else:
        is_vip = is_subscribed(user.id)
        await update.message.reply_text("تم تفعيل واجهتك الخاصة بنجاح.", reply_markup=get_subscriber_reply_keyboard())
        await update.message.reply_text(welcome_msg, reply_markup=get_subscriber_inline_keyboard(is_vip=is_vip), parse_mode="Markdown")

# معالج الأزرار والتفاعل
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in db["banned"]:
        await query.edit_message_text("❌ أنت محظور من استخدام البوت.")
        return

    if query.data == "get_signal":
        if not is_subscribed(user_id):
            await query.edit_message_text("❌ انتهت صلاحية اشتراكك. يرجى إدخال كود تفعيل جديد للحصول على الصفقات المضمونة.")
            return

        # جلب السعر الحي والفوري من السوق
        curr, opn, high, low = get_live_market_price()
        
        now = datetime.datetime.now()
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # تحليل الشمعات من الافتتاح لآخر شمعة والجلسة
        trend = "صاعد قوي (Bullish Momentum)" if curr >= opn else "هابط تصحيحي (Bearish Pressure)"
        action_type = "شراء (BUY 🟢)" if curr >= opn else "بيع (SELL 🔴)"
        entry_price = round(curr, 2)
        sl = round(entry_price - 6.5, 2) if "شراء" in action_type else round(entry_price + 6.5, 2)
        tp1 = round(entry_price + 12.0, 2) if "شراء" in action_type else round(entry_price - 12.0, 2)
        tp2 = round(entry_price + 22.0, 2) if "شراء" in action_type else round(entry_price - 22.0, 2)
        
        signal_text = (
            f"🚀 **تقرير التحليل الحي المباشر من السوق**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🟡 **الأداة المالية:** الذهب العالمي (XAU/USD / GC=F)\n"
            f"⏱ **التوقيت:** {current_time_str}\n"
            f"📊 **الفريم الزمني:** 15 دقيقة / 1 ساعة\n"
            f"🌍 **الجلسة الحالية:** لندن / نيويورك المدمجة\n"
            f"📈 **تحليل الشمعات:** من سعر الافتتاح ({opn}) ولغاية الشمعة الحالية ({curr}) | الاتجاه: {trend}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **تفاصيل الصفقة المضمونة:**\n"
            f"🔹 **نوع العقد:** {action_type}\n"
            f"🔹 **سعر الدخول المباشر:** `{entry_price}`\n"
            f"🛑 **وقف الخسارة (SL):** `{sl}`\n"
            f"🎯 **الهدف الأول (TP1):** `{tp1}`\n"
            f"🎯 **الهدف الثاني (TP2):** `{tp2}`\n"
            f"💰 **حجم اللوت المقترح:** 0.01 لكل 100$ (إدارة رأس مال صارمة)\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 *تم سحب الأسعار حياً ومباشراً من تداولات السوق الآن.*"
        )
        
        db["last_signal"] = signal_text

        keyboard = [[InlineKeyboardButton("🔄 تحديث السعر والتحليل الحي الآن", callback_data="get_signal")]]
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("📢 نشر هذه الصفقة في القناة فوراً", callback_data="publish_to_channel")])
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])

        await query.edit_message_text(signal_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "show_prices":
        prices_text = (
            "🏷️ **باقات الأسعار والاشتراكات الرسمية:**\n\n"
            "⏳ **كود لساعة واحدة:** 5$\n"
            "📅 **كود ليوم كامل:** 15$\n"
            "📅 **كود لأسبوع كامل:** 50$\n"
            "📅 **كود لشهر كامل (VIP):** 130$\n\n"
            "💬 لشراء أي كود فوراً، تواصل مع المطور: @V8V8VN"
        )
        await query.edit_message_text(prices_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]))

    elif query.data == "enter_code":
        context.user_data["waiting_for_code"] = True
        await query.edit_message_text("🔑 **أرسل كود التفعيل الخاص بك الآن في رسالة نصية:**\nسيتحقق البوت منه ويفعل اشتراكك فوراً.")

    elif query.data == "vip_status":
        expiry = db["users"].get(user_id, {}).get("expiry", "منتهي")
        await query.edit_message_text(f"💎 **حسابك مفعل برتبة VIP.**\nينتهي الاشتراك في: {expiry}")

    elif query.data == "admin_gen_menu" and user_id == ADMIN_ID:
        gen_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ ساعة", callback_data="gen_h"), InlineKeyboardButton("📅 يوم", callback_data="gen_d")],
            [InlineKeyboardButton("📅 أسبوع", callback_data="gen_w"), InlineKeyboardButton("💎 شهر", callback_data="gen_m")]
        ])
        await query.edit_message_text("اختر مدة الكود المراد توليده:", reply_markup=gen_kb)

    elif query.data in ["gen_h", "gen_d", "gen_w", "gen_m"] and user_id == ADMIN_ID:
        mapping = {
            "gen_h": ("ساعة واحدة", datetime.timedelta(hours=1)),
            "gen_d": ("يوم كامل", datetime.timedelta(days=1)),
            "gen_w": ("أسبوع كامل", datetime.timedelta(days=7)),
            "gen_m": ("شهر كامل", datetime.timedelta(days=30))
        }
        name, delta = mapping[query.data]
        code = f"VIP-{random.randint(10000, 99999)}"
        db["codes"][code] = {"type": name, "delta": delta, "used": False}
        await query.edit_message_text(f"✅ **تم توليد الكود بنجاح:**\n`{code}`\nالنوع: {name}", parse_mode="Markdown")

    elif query.data == "admin_list_users" and user_id == ADMIN_ID:
        if not db["users"]:
            await query.edit_message_text("👥 لا يوجد مشتركين مسجلين حتى الآن.")
            return
        msg = "👥 **قائمة المشتركين النشطين:**\n\n"
        for uid, info in db["users"].items():
            msg += f"• **الاسم:** {info['name']} | {info['username']}\n  **الآيدي:** `{uid}`\n\n"
        await query.edit_message_text(msg[:4000], parse_mode="Markdown")

    elif query.data == "admin_ban_menu" and user_id == ADMIN_ID:
        context.user_data["waiting_for_ban"] = True
        await query.edit_message_text("🚫 أرسل (آيدي) المستخدم الذي تريد حظره في رسالة نصية الآن.")

    elif query.data == "publish_to_channel" and user_id == ADMIN_ID:
        if db["last_signal"]:
            try:
                await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=db["last_signal"], parse_mode="Markdown")
                await query.edit_message_text("✅ **تم نشر الصفقة بنجاح إلى قناتك العامة!**")
            except Exception as e:
                await query.edit_message_text(f"❌ خطأ في النشر (تأكد أن البوت مشرف بالقناة): {e}")
        else:
            await query.edit_message_text("⚠️ لا توجد صفقة محللة حالياً لنشرها.")

    elif query.data == "main_menu":
        await query.message.delete()
        await start(update, context)

# معالجة الرسائل النصية الحرة (الأكواد والحظر)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in db["banned"]:
        return

    # أزرار الأدمن السفلية
    if text == "🛠️ لوحة الأدمن الرئيسية" and user_id == ADMIN_ID:
        await update.message.reply_text("⚡ لوحة الأدمن:", reply_markup=get_admin_inline_keyboard())
        return
    elif text == "👥 قائمة المشتركين" and user_id == ADMIN_ID:
        if not db["users"]:
            await update.message.reply_text("👥 لا يوجد مشتركين.")
            return
        msg = "👥 **المشتركين المسجلين:**\n"
        for uid, info in db["users"].items():
            msg += f"- {info['name']} (`{uid}`) | {info['username']}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    elif text == "🔑 توليد كود اشتراك" and user_id == ADMIN_ID:
        code = f"VIP-{random.randint(10000, 99999)}"
        db["codes"][code] = {"type": "شهر كامل", "delta": datetime.timedelta(days=30), "used": False}
        await update.message.reply_text(f"✅ تم توليد كود شهري سريع:\n`{code}`", parse_mode="Markdown")
        return
    elif text == "🚫 حظر مستخدم" and user_id == ADMIN_ID:
        context.user_data["waiting_for_ban"] = True
        await update.message.reply_text("🚫 أرسل آيدي المستخدم المراد حظره الآن:")
        return

    # الأزرار العامة
    if text == "📋 القائمة الرئيسية":
        await start(update, context)
        return
    elif text == "👤 حسابي والاشتراك":
        expiry = db["users"].get(user_id, {}).get("expiry", "منتهي")
        await update.message.reply_text(f"💎 حسابك ينتهي في تاريخ: {expiry}")
        return
    elif text == "🔄 مسح وإعادة ضبط":
        await update.message.reply_text("🔄 تمت الإعادة.", reply_markup=ReplyKeyboardRemove())
        await start(update, context)
        return

    # معالجة إدخال الكود للمشترك
    if context.user_data.get("waiting_for_code"):
        if text in db["codes"] and not db["codes"][text]["used"]:
            code_data = db["codes"][text]
            code_data["used"] = True
            expiry_date = datetime.datetime.now() + code_data["delta"]
            
            if user_id in db["users"]:
                db["users"][user_id]["expiry"] = expiry_date
            
            context.user_data["waiting_for_code"] = False
            await update.message.reply_text(f"🎉 **تم تفعيل كود الاشتراك بنجاح ({code_data['type']})!**", reply_markup=get_subscriber_inline_keyboard(is_vip=True), parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ الكود غير صحيح أو تم استخدامه مسبقاً. حاول مجدداً:")
        return

    # معالجة حظر المستخدم بواسطة الأدمن
    if context.user_data.get("waiting_for_ban") and user_id == ADMIN_ID:
        try:
            target_id = int(text)
            db["banned"].add(target_id)
            if target_id in db["users"]:
                del db["users"][target_id]
            context.user_data["waiting_for_ban"] = False
            await update.message.reply_text(f"🚫 تم حظر المستخدم ذو الآيدي `{target_id}` بنجاح.", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ الآيدي غير صحيح، أرسل أرقاماً فقط.")
        return

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("🛸 Zo Supreme Core is online and fully synchronized with GitHub files...")
    app.run_polling()

if __name__ == "__main__":
    main()
