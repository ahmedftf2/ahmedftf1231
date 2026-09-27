import os
import json
import logging
import random
from datetime import datetime

# ==================== مكتبة إدارة الملفات والمسارات ====================
class PathManager:
    @staticmethod
    def create_directories(base_dir, folders):
        os.makedirs(base_dir, exist_ok=True)
        for folder in folders:
            path = os.path.join(base_dir, folder)
            os.makedirs(path, exist_ok=True)

# ==================== مكتبة إدارة السجلات (Logging) ====================
class LoggerManager:
    @staticmethod
    def get_logger(name="VIP_Core"):
        logging.basicConfig(
            format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        return logging.getLogger(name)

# ==================== مكتبة إدارة قواعد البيانات المحلية (JSON) ====================
class DatabaseManager:
    def __init__(self, filepath="database/storage.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            self._write_data({})

    def _read_data(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_data(self, data):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def set_item(self, key, value):
        data = self._read_data()
        data[key] = value
        self._write_data(data)

    def get_item(self, key):
        data = self._read_data()
        return data.get(key)

# ==================== مكتبة التوليد الأمني وتشفير البيانات ====================
class SecurityManager:
    @staticmethod
    def generate_vip_key(prefix="VIP"):
        return f"{prefix}-{random.randint(100000, 999999)}"

    @staticmethod
    def get_current_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
