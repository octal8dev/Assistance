"""
Главный файл телеграм бота - AI ассистент
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Добавляем путь к src в PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import NetworkError, TelegramError

# Импорты нашего проекта
from config import config
from src.database import init_database, close_database, db_manager
from src.services import bot_gpt_service, human_behavior_service
from src.bot import command_handlers
from src.utils import setup_logging, rate_limiter

# Настройка логирования
logger = setup_logging(config.LOG_LEVEL, config.LOG_FILE)

class TelegramBot:
    """Основной класс телеграм бота"""
    
    def __init__(self):
        self.application = None
        self.is_running = False
        
        # Валидируем конфигурацию
        if not config.validate():
            logger.error("❌ Конфигурация не прошла валидацию!")
            sys.exit(1)
        
        logger.info("✅ Конфигурация валидна")
        logger.info(f"🔑 Администраторы: {config.TELEGRAM_ADMIN_IDS}")
    
    async def initialize(self):
        """Инициализация бота и всех компонентов"""
        try:
            logger.info("🚀 Инициализация телеграм бота...")
            
            # ПЕРВЫМ ДЕЛОМ - инициализация Telethon с авторизацией через аккаунт
            logger.info("🤖 Инициализация сервиса человеческого поведения...")
            print("\n" + "🔥"*60)
            print("ОБЯЗАТЕЛЬНАЯ АВТОРИЗАЦИЯ TELETHON ЧЕРЕЗ АККАУНТ")
            print("🔥"*60)
            
            telethon_success = await human_behavior_service.initialize()
            if not telethon_success:
                logger.error("❌ Не удалось инициализировать Telethon! Бот не будет запущен.")
                print("❌ ОШИБКА: Telethon не инициализирован - бот не запустится!")
                sys.exit(1)
            
            print("🔥"*60)
            print("✅ TELETHON АВТОРИЗОВАН - ПРОДОЛЖАЕМ ЗАПУСК БОТА")
            print("🔥"*60)
            
            # Инициализация базы данных
            logger.info("💾 Подключение к базе данных...")
            await init_database(config.DATABASE_URL)
            logger.info("✅ База данных подключена успешно")
            
            # Создание приложения Telegram
            logger.info("📱 Создание Telegram приложения...")
            self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
            
            # Регистрация обработчиков команд
            self._register_handlers()
            
            # Регистрация обработчиков ошибок
            self.application.add_error_handler(self._error_handler)
            
            logger.info("✅ Телеграм бот инициализирован успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации бота: {e}")
            raise
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        logger.info("📋 Регистрация обработчиков команд...")
        
        # Основные команды
        self.application.add_handler(CommandHandler("start", command_handlers.start_command))
        self.application.add_handler(CommandHandler("help", command_handlers.help_command))
        self.application.add_handler(CommandHandler("ask", command_handlers.ask_command))
        self.application.add_handler(CommandHandler("status", command_handlers.status_command))
        self.application.add_handler(CommandHandler("stats", command_handlers.stats_command))
        
        # Администраторские команды
        self.application.add_handler(CommandHandler("admin", command_handlers.admin_command))
        self.application.add_handler(CommandHandler("reset", command_handlers.reset_command))
        self.application.add_handler(CommandHandler("providers", command_handlers.providers_command))
        
        # Обработчик инлайн-кнопок
        self.application.add_handler(CallbackQueryHandler(command_handlers.handle_callback_query))
        
        # Обработчик обычных сообщений (для режима вопросов)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, command_handlers.handle_message)
        )
        
        # Обработчик сообщений с фото
        self.application.add_handler(
            MessageHandler(filters.PHOTO, command_handlers.handle_message)
        )
        
        logger.info("✅ Обработчики зарегистрированы")
    
    async def _error_handler(self, update: Update, context):
        """Обработчик ошибок"""
        error = context.error
        
        if isinstance(error, NetworkError):
            logger.warning(f"🌐 Сетевая ошибка: {error}")
        elif isinstance(error, TelegramError):
            logger.error(f"📱 Ошибка Telegram: {error}")
        else:
            logger.error(f"❌ Неожиданная ошибка: {error}", exc_info=True)
        
        # Отправляем сообщение пользователю, если возможно
        if update and update.effective_user:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🚫 Произошла ошибка при обработке запроса. Попробуйте позже."
                )
            except Exception:
                pass  # Игнорируем ошибки при отправке сообщения об ошибке
    
    async def start(self):
        """Запуск бота"""
        try:
            await self.initialize()
            
            logger.info("🔄 Запуск бота...")
            self.is_running = True
            
            # Запускаем бота
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            logger.info("✅ Бот запущен и работает!")
            logger.info("📱 Ожидание сообщений...")
            
            # Периодическая очистка rate limiter
            asyncio.create_task(self._cleanup_task())
            
            # Ждем сигнала остановки
            await self._wait_for_shutdown()
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Остановка бота"""
        logger.info("🛑 Остановка бота...")
        self.is_running = False
        
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("📱 Telegram приложение остановлено")
            
            # Закрываем Telethon соединение
            await human_behavior_service.close()
            
            # Закрываем соединение с БД
            await close_database()
            logger.info("💾 Соединение с базой данных закрыто")
            
            logger.info("✅ Бот остановлен успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке бота: {e}")
    
    async def _cleanup_task(self):
        """Периодическая очистка rate limiter"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Каждый час
                if self.is_running:
                    rate_limiter.cleanup()
                    logger.info("🧹 Выполнена очистка rate limiter")
            except Exception as e:
                logger.error(f"❌ Ошибка при очистке rate limiter: {e}")
    
    async def _wait_for_shutdown(self):
        """Ожидание сигнала остановки"""
        stop_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info(f"📡 Получен сигнал {signum}")
            stop_event.set()
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Ждем сигнала остановки
        await stop_event.wait()

async def main():
    """Главная функция"""
    bot = TelegramBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🔌 Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверяем версию Python
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔌 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
