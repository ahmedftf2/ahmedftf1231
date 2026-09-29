from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# الأيدي الخاص بك كأدمن مطلق (أحمد السيد)
ADMIN_ID = 5796443586

# لوحة المفاتيح السفلية (قريب الكيبورد)
def get_reply_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📋 القائمة الرئيسية"), KeyboardButton("🗑️ مسح وإعادة ضبط السجل")]
        ],
        resize_keyboard=True
    )

# أزرار المشتركين (العامة)
def get_subscriber_keyboard(is_vip=False):
    vip_status_text = "💎 رتبة VIP مفعلة" if is_vip else "🔑 إضافة كود (تفعيل رخصة الاشتراك)"
    callback_target = "vip_info" if is_vip else "add_code"
    
    keyboard = [
        [InlineKeyboardButton("📊 تحليل الذهب والصفقات الجاهزة (100%)", callback_data="gold_analysis")],
        [InlineKeyboardButton("📸 إرسال سكرين الشاشة للتحليل الأسطوري", callback_data="screen_analysis")],
        [InlineKeyboardButton(vip_status_text, callback_data=callback_target)],
        [InlineKeyboardButton("💬 راسل المطور الأسطوري", url="https://t.me/V8V8VN")],
        [
            InlineKeyboardButton("📸 انستغرام", url="https://instagram.com"),
            InlineKeyboardButton("🎵 تيك توك", url="https://tiktok.com")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# أزرار لوحة تحكم الأدمن الحصرية لك وحدك يا أحمد
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛠️ لوحة القيادة الإدارية لكبار الشخصيات [VIP]", callback_data="admin_vip_panel")],
        [InlineKeyboardButton("⚡ استخراج الصفقة الملكية والثغرات (%1M)", callback_data="admin_glitch")],
        [InlineKeyboardButton("📈 العالمي + الأخبار [M5]", callback_data="admin_news")],
        [InlineKeyboardButton("💎 إدارة وتوليد الأكواد الجديدة", callback_data="admin_generate_code")],
        [InlineKeyboardButton("🏷️ باقات وقائمة أسعار VIP الفاخرة", callback_data="admin_prices")],
        [InlineKeyboardButton("➕ تفعيل رخصة اشتراك جديدة يدوياً", callback_data="admin_new_license")],
    ]
    return InlineKeyboardMarkup(keyboard)
