"""
Сервис для эмуляции человеческого поведения бота с использованием Telethon
"""
import asyncio
import logging
import random
from typing import Optional, Union
from telethon import TelegramClient, errors
from telethon.tl.types import User
from config import config

logger = logging.getLogger(__name__)

class HumanBehaviorService:
    """Сервис для эмуляции человеческого поведения"""
    
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.is_initialized = False
        
    async def initialize(self):
        """Инициализация Telethon клиента для аккаунта пользователя (не бота)"""
        try:
            if config.TELETHON_API_ID == 0 or not config.TELETHON_API_HASH:
                logger.warning("🤖 Telethon не настроен - работаем без эмуляции человеческого поведения")
                return False

            if not config.TELETHON_PHONE_NUMBER:
                logger.error("❌ TELETHON_PHONE_NUMBER не задан!")
                return False

            self.client = TelegramClient(
                config.TELETHON_SESSION_STRING,
                config.TELETHON_API_ID,
                config.TELETHON_API_HASH
            )

            # Авторизация ТОЛЬКО через аккаунт пользователя
            logger.info(f"📱 Авторизация Telethon через аккаунт: {config.TELETHON_PHONE_NUMBER}")
            print("\n" + "="*60)
            print("📱 ИНИЦИАЛИЗАЦИЯ TELETHON")
            print("="*60)
            print(f"📞 Авторизуемся как пользователь: {config.TELETHON_PHONE_NUMBER}")
            print("📱 Приготовьтесь ввести код из Telegram")
            print("="*60)
            
            await self.client.start(
                phone=config.TELETHON_PHONE_NUMBER,
                code_callback=self._code_callback,
                password=self._password_callback
            )
            
            self.is_initialized = True
            
            # Получаем информацию о пользователе
            me = await self.client.get_me()
            logger.info(f"🎭 Telethon инициализирован для пользователя: @{me.username if me.username else me.first_name}")
            print("="*60)
            print("✅ TELETHON УСПЕШНО ИНИЦИАЛИЗИРОВАН!")
            print(f"👤 Пользователь: @{me.username if me.username else me.first_name}")
            print("🤖 Эмуляция человеческого поведения активна")
            print("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Telethon: {e}")
            self.is_initialized = False
            return False
    
    async def _code_callback(self):
        """Callback для ввода кода авторизации"""
        logger.info("📱 Telethon требует код авторизации!")
        logger.info("🔔 Проверьте Telegram на наличие кода авторизации")
        print("\n" + "="*50)
        print("📱 TELETHON АВТОРИЗАЦИЯ")
        print("="*50)
        print("� Проверьте ваш Telegram на код авторизации")
        print(f"📞 Номер телефона: {config.TELETHON_PHONE_NUMBER}")
        print("="*50)
        
        # Запрашиваем код у пользователя через консоль
        code = input("Введите код из Telegram: ").strip()
        
        if code:
            logger.info(f"✅ Получен код авторизации: {code}")
            return code
        else:
            logger.error("❌ Код не введен")
            return None
    
    async def _password_callback(self):
        """Callback для ввода пароля (если включена двухфакторная аутентификация)"""
        logger.info("🔐 Telethon требует пароль двухфакторной аутентификации!")
        print("\n" + "="*50)
        print("🔐 ДВУХФАКТОРНАЯ АУТЕНТИФИКАЦИЯ")
        print("="*50)
        print("🔑 Пароль для 2FA будет подставлен автоматически")
        print("="*50)
        password = "Agsh@#uwi181"
        logger.info("✅ Пароль 2FA подставлен автоматически")
        return password
    
    async def close(self):
        """Закрытие соединения"""
        if self.client and self.is_initialized:
            await self.client.disconnect()
            logger.info("🔌 Telethon клиент отключен")
    
    def generate_response_delay(self) -> int:
        """Генерирует случайную задержку ответа от 1 до 3 минут"""
        return random.randint(config.MIN_RESPONSE_DELAY, config.MAX_RESPONSE_DELAY)
    
    def generate_typing_delay(self) -> int:
        """Генерирует случайную задержку печатания"""
        return random.randint(config.TYPING_DELAY_MIN, config.TYPING_DELAY_MAX)
    
    async def simulate_human_typing(self, chat_id: Union[int, str], typing_duration: Optional[int] = None):
        """
        Имитирует печатание человека
        
        Args:
            chat_id: ID чата
            typing_duration: Длительность печатания в секундах (если не указано, генерируется случайно)
        """
        if not self.is_initialized:
            return
        
        try:
            if typing_duration is None:
                typing_duration = self.generate_typing_delay()
            
            logger.info(f"⌨️ Имитируем печатание в чате {chat_id} в течение {typing_duration} секунд")
            
            # Отправляем статус "печатает"
            async with self.client.action(chat_id, 'typing'):
                await asyncio.sleep(typing_duration)
                
        except Exception as e:
            logger.error(f"❌ Ошибка при имитации печатания: {e}")
    
    async def simulate_human_delay(self, message_text: str = "") -> int:
        """
        Имитирует человеческую задержку перед ответом
        
        Args:
            message_text: Текст сообщения для адаптивной задержки
            
        Returns:
            Количество секунд задержки
        """
        # Базовая задержка
        base_delay = self.generate_response_delay()
        
        # Адаптивная задержка в зависимости от длины сообщения
        if message_text:
            # Добавляем до 30 секунд для длинных сообщений
            message_length_factor = min(len(message_text) // 100, 30)
            base_delay += message_length_factor
        
        logger.info(f"⏰ Задержка ответа: {base_delay} секунд ({base_delay/60:.1f} минут)")
        return base_delay
    
    async def send_message_with_human_behavior(
        self, 
        chat_id: Union[int, str], 
        message: str,
        pre_typing_delay: Optional[int] = None
    ):
        """
        Отправляет сообщение с имитацией человеческого поведения
        
        Args:
            chat_id: ID чата
            message: Текст сообщения
            pre_typing_delay: Задержка перед началом печатания
        """
        if not self.is_initialized:
            logger.warning("⚠️ Telethon не инициализирован - отправляем без эмуляции")
            return
        
        try:
            # Задержка перед началом печатания
            if pre_typing_delay:
                logger.info(f"⏸️ Ждем {pre_typing_delay} секунд перед ответом...")
                await asyncio.sleep(pre_typing_delay)
            
            # Имитируем печатание
            typing_duration = self.calculate_typing_duration(message)
            await self.simulate_human_typing(chat_id, typing_duration)
            
            # Отправляем сообщение через Telethon
            await self.client.send_message(chat_id, message)
            logger.info(f"📤 Сообщение отправлено в чат {chat_id} через Telethon")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения через Telethon: {e}")
            raise
    
    def calculate_typing_duration(self, message: str) -> int:
        """
        Вычисляет длительность печатания на основе длины сообщения
        
        Args:
            message: Текст сообщения
            
        Returns:
            Длительность печатания в секундах
        """
        # Базовая скорость: ~40 слов в минуту или ~200 символов в минуту
        words_count = len(message.split())
        chars_count = len(message)
        
        # Время на основе количества слов (40 слов/мин)
        time_by_words = (words_count / 40) * 60
        
        # Время на основе символов (200 символов/мин)
        time_by_chars = (chars_count / 200) * 60
        
        # Берем среднее и добавляем случайность
        base_time = (time_by_words + time_by_chars) / 2
        
        # Добавляем случайность ±50%
        random_factor = random.uniform(0.5, 1.5)
        typing_time = int(base_time * random_factor)
        
        # Ограничиваем время печатания
        min_typing = config.TYPING_DELAY_MIN
        max_typing = min(config.TYPING_DELAY_MAX, 120)  # максимум 2 минуты на печатание
        
        typing_time = max(min_typing, min(typing_time, max_typing))
        
        logger.debug(f"📝 Рассчитанное время печатания: {typing_time} секунд для сообщения из {chars_count} символов")
        
        return typing_time
    
    async def mark_as_read(self, chat_id: Union[int, str]):
        """
        Отмечает сообщения как прочитанные
        
        Args:
            chat_id: ID чата
        """
        if not self.is_initialized:
            return
        
        try:
            await self.client.send_read_acknowledge(chat_id)
            logger.debug(f"👁️ Сообщения отмечены как прочитанные в чате {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отметки сообщений как прочитанных: {e}")

# Глобальный экземпляр сервиса
human_behavior_service = HumanBehaviorService()
