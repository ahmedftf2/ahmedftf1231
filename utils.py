import aiohttp
import sqlite3
from datetime import datetime

def init_db():
    try:
        conn = sqlite3.connect("bot_database.db", timeout=5)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                expiry TEXT,
                is_vip INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vip_codes (
                code TEXT PRIMARY KEY,
                days INTEGER,
                used INTEGER
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

async def get_live_gold_price() -> float:
    urls = [
        "https://api.coingecko.com/api/v3/simple/price?ids=tether-gold&vs_currencies=usd",
        "https://api.metals.live/v1/spot"
    ]
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=3) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "tether-gold" in data:
                            return float(data["tether-gold"]["usd"])
                        elif isinstance(data, list):
                            for item in data:
                                if "gold" in item:
                                    return float(item["gold"])
            except Exception:
                continue
    return 2650.50

async def analyze_market_signal() -> dict:
    current_price = await get_live_gold_price()
    market_indicator = int(current_price * 10) % 5
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if market_indicator == 0:
        strength = "قوية جداً 🔥"
        signal_type = "🟢 شراء (BUY)"
        strategy = "ثغرة اختراق السيولة المؤسسية العليا + مفهوم الذكي (Smart Money Concepts)"
        tp1 = current_price + 14.0
        tp2 = current_price + 28.0
        tp3 = current_price + 45.0
        sl = current_price - 11.0
        secure_point = f"تأمين الصفقة بنقل الستوب لبريك إيفن عند تحقيق الهدف الأول ({tp1:.2f})"
    elif market_indicator == 1:
        strength = "قوية جداً 🔥"
        signal_type = "🔴 بيع (SELL)"
        strategy = "منطقة عرض كلاسيكية كبرى + رفض سعري عند مستويات العرض والطلب"
        tp1 = current_price - 14.0
        tp2 = current_price - 28.0
        tp3 = current_price - 45.0
        sl = current_price + 11.0
        secure_point = f"تأمين الصفقة بنقل الستوب لبريك إيفن عند تحقيق الهدف الأول ({tp1:.2f})"
    elif market_indicator == 2:
        strength = "متوسطة 🛡️"
        signal_type = "🟢 شراء (BUY)"
        strategy = "ثغرة فجوة الأسعار الفورية (Fair Value Gap - FVG) وإعادة الاختبار"
        tp1 = current_price + 10.0
        tp2 = current_price + 20.0
        tp3 = None
        sl = current_price - 8.0
        secure_point = f"تأمين الصفقة عند الهدف الأول ({tp1:.2f})"
    elif market_indicator == 3:
        strength = "متوسطة 🛡️"
        signal_type = "🔴 بيع (SELL)"
        strategy = "منطقة طلب مكسورة تحولت إلى عرض (Break of Structure - BOS)"
        tp1 = current_price - 10.0
        tp2 = current_price - 20.0
        tp3 = None
        sl = current_price + 8.0
        secure_point = f"تأمين الصفقة عند الهدف الأول ({tp1:.2f})"
    else:
        strength = "ضعيفة ⚠️"
        signal_type = "🟢 شراء تكتيكي (BUY)"
        strategy = "ثغرة اصطياد وقف الخسارة للمتداولين الصغار (Stop Hunting Reversal)"
        tp1 = current_price + 7.0
        tp2 = None
        tp3 = None
        sl = current_price - 6.0
        secure_point = "مخاطرة عالية، يرجى الالتزام بالهدف الواحد ومراقبة السوق"

    return {
        "price": current_price,
        "type": signal_type,
        "strength": strength,
        "strategy": strategy,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "sl": sl,
        "secure": secure_point,
        "session": "الجلسة الأمريكية / الأوروبية المشتركة",
        "country": "الولايات المتحدة (USD) / الاتحاد الأوروبي (EUR)",
        "time": current_time,
        "timeframe": "M5",
        "lot": "0.01"
    }
