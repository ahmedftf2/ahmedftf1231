from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

ADMIN_ID = 5796443586
CHANNEL_USERNAME = "@YourChannelUsername"

# الكيبورد الثابت السفلي بجانب خانة الكتابة (يحتوي على زر التشغيل/البداية)
def get_persistent_reply_keyboard():
    keyboard = [
        [KeyboardButton("🚀 تشغيل /start واللوحة الرئيسية")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

# الأزرار التفاعلية التي تظهر فوق الكيبورد تماماً كلوحة الأوامر
def get_main_control_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("📊 استخراج الصفقة الملكية (منع العكس تماماً 1M%)", callback_data="menu_analysis")],
        [InlineKeyboardButton("🔄 تحديث الصفقة والسعر الحي", callback_data="menu_update")],
        [InlineKeyboardButton("⏱️ الفريم: [M5]", callback_data="menu_settings"), InlineKeyboardButton("🌐 العالمي + الأخبار", callback_data="menu_news")],
        [InlineKeyboardButton("⚖️ اللوت: [0.01]", callback_data="menu_lot")],
        [InlineKeyboardButton("💎 باقات وقائمة أسعار VIP الفاخرة", callback_data="menu_pricing")],
        [InlineKeyboardButton("🔑 تفعيل رخصة اشتراك جديدة", callback_data="menu_activate")]
    ]
    if is_admin:
        keyboard.insert(0, [InlineKeyboardButton("⚙️ لوحة القيادة الإدارية لكبار الشخصيات [VIP]", callback_data="menu_admin")])
    
    return InlineKeyboardMarkup(keyboard)

def get_timeframes_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱️ فريم 1 دقيقة", callback_data="tf_1m"), InlineKeyboardButton("⏱️ فريم 5 دقائق", callback_data="tf_5m")],
        [InlineKeyboardButton("⏱️ فريم 15 دقيقة", callback_data="tf_15m"), InlineKeyboardButton("⏱️ فريم 1 ساعة", callback_data="tf_1h")],
        [InlineKeyboardButton("⏱️ فريم 4 ساعات", callback_data="tf_4h")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]
    ])

def get_lots_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 0.01", callback_data="lot_0.01"), InlineKeyboardButton("🔹 0.03", callback_data="lot_0.03"), InlineKeyboardButton("🔹 0.05", callback_data="lot_0.05")],
        [InlineKeyboardButton("🔹 0.10", callback_data="lot_0.10"), InlineKeyboardButton("🔹 0.20", callback_data="lot_0.20"), InlineKeyboardButton("🔹 0.30", callback_data="lot_0.30")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]
    ])

def get_admin_inline_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎟️ كود ساعة (10)", callback_data="admin_gen_1h")],
        [InlineKeyboardButton("🎟️ كود يومي (25)", callback_data="admin_gen_1d")],
        [InlineKeyboardButton("🎟️ كود أسبوعي (75)", callback_data="admin_gen_7d")],
        [InlineKeyboardButton("🎟️ كود أسبوعين (125)", callback_data="admin_gen_14d")],
        [InlineKeyboardButton("🎟️ كود شهر VIP (225)", callback_data="admin_gen_30d")],
        [InlineKeyboardButton("👥 قائمة المشتركين", callback_data="admin_list_users")],
        [InlineKeyboardButton("📢 نشر للقناة العامة", callback_data="publish_to_channel")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="menu_start")]
    ])
