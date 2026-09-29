from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

ADMIN_ID = 5796443586
CHANNEL_USERNAME = "@YourChannelUsername" # ضع معرف قناتك هنا

# لوحة التحكم الخاصة بك كأدمن
def get_admin_reply_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🛠️ لوحة الأدمن الرئيسية"), KeyboardButton("👥 قائمة المشتركين")],
            [KeyboardButton("🔑 توليد كود اشتراك"), KeyboardButton("🚫 حظر مستخدم")],
            [KeyboardButton("📋 القائمة الرئيسية")]
        ],
        resize_keyboard=True
    )

# لوحة المشترك العادي
def get_subscriber_reply_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📋 القائمة الرئيسية"), KeyboardButton("👤 حسابي والاشتراك")],
            [KeyboardButton("🔄 مسح وإعادة ضبط")]
        ],
        resize_keyboard=True
    )

# أزرار واجهة المشترك (Inline)
def get_subscriber_inline_keyboard(is_vip=False):
    vip_text = "💎 رتبة VIP مفعلة" if is_vip else "🔑 إدخال كود التفعيل"
    target_data = "vip_status" if is_vip else "enter_code"
    
    keyboard = [
        [InlineKeyboardButton("📊 تحليل الذهب والصفقة الحية المضمونة", callback_data="get_signal")],
        [InlineKeyboardButton("🏷️ عرض باقات الأسعار", callback_data="show_prices")],
        [InlineKeyboardButton(vip_text, callback_data=target_data)],
        [InlineKeyboardButton("📢 قناة البوت الرسمية", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("💬 مراسلة المطور أحمد السيد", url="https://t.me/V8V8VN")]
    ]
    return InlineKeyboardMarkup(keyboard)

# أزرار لوحة تحكم الأدمن (Inline)
def get_admin_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ توليد كود (ساعة/يوم/أسبوع/شهر)", callback_data="admin_gen_menu")],
        [InlineKeyboardButton("👥 عرض المشتركين بالأسماء والآيدي", callback_data="admin_list_users")],
        [InlineKeyboardButton("🚫 حظر مستخدم من البوت", callback_data="admin_ban_menu")],
        [InlineKeyboardButton("📢 نشر آخر صفقة للقناة يدوياً", callback_data="publish_to_channel")]
    ]
    return InlineKeyboardMarkup(keyboard)
