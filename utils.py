from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

ADMIN_ID = 5796443586
CHANNEL_USERNAME = "@YourChannelUsername"

def get_main_control_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton("📊 تحليل استراتيجي شامل (مدارس وثغرات)"), KeyboardButton("📸 تحليل سكرين الشاشة")],
        [KeyboardButton("⚙️ اختيار الفريم وحجم اللوت"), KeyboardButton("👤 حسابي والاشتراك")],
        [KeyboardButton("📋 القائمة الرئيسية"), KeyboardButton("🔄 إعادة ضبط")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton("👑 لوحة السيطرة الإمبراطورية للأدمن")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_timeframes_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱️ فريم 1 دقيقة", callback_data="tf_1m"), InlineKeyboardButton("⏱️ فريم 5 دقائق", callback_data="tf_5m")],
        [InlineKeyboardButton("⏱️ فريم 15 دقيقة", callback_data="tf_15m"), InlineKeyboardButton("⏱️ فريم 1 ساعة", callback_data="tf_1h")],
        [InlineKeyboardButton("⏱️ فريم 4 ساعات", callback_data="tf_4h")]
    ])

def get_lots_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 0.01", callback_data="lot_0.01"), InlineKeyboardButton("🔹 0.03", callback_data="lot_0.03"), InlineKeyboardButton("🔹 0.05", callback_data="lot_0.05")],
        [InlineKeyboardButton("🔹 0.10", callback_data="lot_0.10"), InlineKeyboardButton("🔹 0.20", callback_data="lot_0.20"), InlineKeyboardButton("🔹 0.30", callback_data="lot_0.30")]
    ])

def get_admin_inline_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ توليد كود تفعيل VIP", callback_data="admin_gen_code")],
        [InlineKeyboardButton("👥 قائمة المشتركين بالكامل", callback_data="admin_list_users")],
        [InlineKeyboardButton("📢 نشر آخر تحليل للقناة العامة", callback_data="publish_to_channel")]
    ])
