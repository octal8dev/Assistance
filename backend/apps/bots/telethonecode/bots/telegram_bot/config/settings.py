"""
Конфигурация приложения
"""
import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Основная конфигурация приложения"""
    
    # Telegram настройки
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_ADMIN_IDS_STR = os.getenv('TELEGRAM_ADMIN_IDS', '')
    HUMAN_TAG_USER_ID = int(os.getenv('HUMAN_TAG_USER_ID', '0'))
    
    # Telethon настройки для эмуляции человеческого поведения
    TELETHON_API_ID = int(os.getenv('TELETHON_API_ID', '0'))
    TELETHON_API_HASH = os.getenv('TELETHON_API_HASH', '')
    TELETHON_SESSION_STRING = os.getenv('TELETHON_SESSION_STRING', 'bot_session')
    TELETHON_PHONE_NUMBER = os.getenv('TELETHON_PHONE_NUMBER', '')
    
    # Настройки задержек для эмуляции человеческого поведения
    MIN_RESPONSE_DELAY = int(os.getenv('MIN_RESPONSE_DELAY', '60'))  # минимум 1 минута
    MAX_RESPONSE_DELAY = int(os.getenv('MAX_RESPONSE_DELAY', '180'))  # максимум 3 минуты
    TYPING_DELAY_MIN = int(os.getenv('TYPING_DELAY_MIN', '5'))  # минимальная задержка печатания
    TYPING_DELAY_MAX = int(os.getenv('TYPING_DELAY_MAX', '15'))  # максимальная задержка печатания
    
    @property
    def TELEGRAM_ADMIN_IDS(self) -> List[int]:
        """Список ID администраторов"""
        if not self.TELEGRAM_ADMIN_IDS_STR:
            return []
        try:
            return [int(uid.strip()) for uid in self.TELEGRAM_ADMIN_IDS_STR.split(',') if uid.strip()]
        except ValueError:
            return []
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/telegram_bot_db')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'telegram_bot_db')
    DB_USER = os.getenv('DB_USER', 'username')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # GPT сервис
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-4')
    USE_PROXY = os.getenv('USE_PROXY', 'False').lower() == 'true'
    PROXY_URL = os.getenv('PROXY_URL', '')
    
    # Ограничения
    MAX_REQUESTS_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '10'))
    MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '4000'))
    
    # Валидация критических настроек
    def validate(self) -> bool:
        """Проверка корректности конфигурации"""
        if not self.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN не задан!")
            return False
        
        if not self.TELEGRAM_ADMIN_IDS:
            print("❌ TELEGRAM_ADMIN_IDS не заданы!")
            return False
        
        if not self.DATABASE_URL:
            print("❌ DATABASE_URL не задан!")
            return False
        
        # Проверяем настройки Telethon (опциональные для базовой работы)
        if self.TELETHON_API_ID == 0:
            print("⚠️  TELETHON_API_ID не задан - человеческое поведение не будет работать")
        
        if not self.TELETHON_API_HASH:
            print("⚠️  TELETHON_API_HASH не задан - человеческое поведение не будет работать")
        
        if not self.TELETHON_PHONE_NUMBER:
            print("⚠️  TELETHON_PHONE_NUMBER не задан - может потребоваться ручная авторизация")
        
        return True

# Глобальный экземпляр конфигурации
config = Config()
