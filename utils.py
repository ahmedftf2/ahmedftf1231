from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

ADMIN_ID = 5796443586
CHANNEL_USERNAME = "@YourChannelUsername"

# لوحة الأدمن والمشتركين التي تحتوي على زري التحليل وسكرين الشاشة
def get_main_control_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton("📊 تحليل السوق والصفقة الحية المباشرة")],
        [KeyboardButton("📸 تحليل شاشة السوق (سكرين شاشة)"), KeyboardButton("👤 حسابي والاشتراك")],
        [KeyboardButton("📋 القائمة الرئيسية"), KeyboardButton("🔄 تحديث عام")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton("👑 لوحة الأدمن ونشر القناة")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_inline_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ توليد كود اشتراك جديد", callback_data="admin_gen_code")],
        [InlineKeyboardButton("👥 عرض المشتركين بالبوت", callback_data="admin_list_users")],
        [InlineKeyboardButton("📢 نشر آخر صفقة للقناة الآن", callback_data="publish_to_channel")]
    ])
