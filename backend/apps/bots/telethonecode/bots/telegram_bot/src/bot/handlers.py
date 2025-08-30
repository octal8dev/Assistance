"""
Обработчики команд для телеграм бота
"""
import asyncio
import logging
import time
from typing import Optional
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode, ChatAction

from ..database import db_manager
from ..services import bot_gpt_service, human_behavior_service
from ..utils import rate_limiter, format_duration, split_long_message, complexity_analyzer
from config import config

logger = logging.getLogger(__name__)

class CommandHandlers:
    """Класс для обработки команд телеграм бота"""
    
    def __init__(self):
        self.gpt_service = bot_gpt_service
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        logger.info(f"[START] Команда /start от пользователя {user.id} ({user.username})")
        
        # Проверяем, является ли пользователь администратором
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            await update.message.reply_text(
                "🚫 Доступ запрещен. Этот бот работает только для авторизованных пользователей.",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.warning(f"[ACCESS_DENIED] Пользователь {user.id} не в списке администраторов")
            return
        
        # Регистрируем пользователя и чат в базе данных
        if db_manager:
            try:
                await db_manager.get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_admin=True
                )
                
                await db_manager.get_or_create_chat(
                    chat_id=chat.id,
                    chat_type=chat.type,
                    title=getattr(chat, 'title', None)
                )
                
                logger.info(f"[DB] Пользователь {user.id} и чат {chat.id} зарегистрированы в БД")
            except Exception as e:
                logger.error(f"[DB_ERROR] Ошибка регистрации в БД: {e}")
        
        # Приветственное сообщение с кнопками
        welcome_text = f"""🤖 *Добро пожаловать, {user.first_name or user.username}!*

Я ваш AI ассистент. Выберите действие:

_Поддерживается работа с изображениями и историей разговоров._"""

        # Создаем инлайн-клавиатуру
        keyboard = [
            [
                InlineKeyboardButton("❓ Задать вопрос", callback_data="action_ask"),
                InlineKeyboardButton("📊 Статус", callback_data="action_status")
            ],
            [
                InlineKeyboardButton("📈 Моя статистика", callback_data="action_stats"),
                InlineKeyboardButton("🔧 Админ панель", callback_data="action_admin")
            ],
            [
                InlineKeyboardButton("🤖 Провайдеры", callback_data="action_providers"),
                InlineKeyboardButton("ℹ️ Справка", callback_data="action_help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        user = update.effective_user
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            return
        
        help_text = """🔍 *Справка по командам AI ассистента*

*📝 Основные команды:*
• `/start` - Начать работу с ботом
• `/ask [вопрос]` - Задать вопрос AI ассистенту
• `/help` - Показать эту справку
• `/status` - Проверить статус системы
• `/stats` - Ваша персональная статистика

*🔧 Администраторские команды:*
• `/admin` - Панель администратора
• `/reset [user_id]` - Сбросить лимиты для пользователя
• `/providers` - Информация о AI провайдерах

*💡 Примеры команды /ask:*
```
/ask Что такое машинное обучение?
/ask Напиши функцию на Python для поиска простых чисел
/ask Объясни разницу между SQL и NoSQL базами данных
/ask Как создать REST API на FastAPI?
```

*🖼️ Работа с изображениями:*
Отправьте изображение с командой `/ask` и текстом для анализа изображения.

*⚡ Ограничения:*
• Максимум {config.MAX_REQUESTS_PER_MINUTE} запросов в минуту
• Максимальная длина ответа: {config.MAX_MESSAGE_LENGTH} символов
• Поддерживается история разговоров

_Бот работает 24/7 и сохраняет историю всех разговоров._""".format(config=config)

        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        
        logger.info(f"[HELP] Показана справка пользователю {user.id}")
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /ask - работает везде с эмуляцией человеческого поведения"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            await message.reply_text("🚫 Доступ запрещен.")
            return
        
        # Проверяем rate limiting
        is_allowed, error_msg = rate_limiter.is_allowed(
            user.id, 
            max_requests=config.MAX_REQUESTS_PER_MINUTE,
            time_window=60
        )
        
        if not is_allowed:
            await message.reply_text(f"⏱️ {error_msg}")
            logger.warning(f"[RATE_LIMIT] Пользователь {user.id} превысил лимит: {error_msg}")
            return
        
        # Извлекаем текст вопроса
        question_text = ""
        if context.args:
            question_text = " ".join(context.args)
        
        # Проверяем наличие изображения
        image_data = None
        if message.photo:
            try:
                # Получаем изображение наибольшего размера
                photo = message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                
                # Скачиваем изображение
                import io
                import base64
                
                image_bytes = io.BytesIO()
                await file.download_to_memory(image_bytes)
                image_bytes.seek(0)
                
                # Конвертируем в base64
                image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
                image_data = f"data:image/jpeg;base64,{image_base64}"
                
                logger.info(f"[IMAGE] Получено изображение от пользователя {user.id}")
                
                if not question_text:
                    question_text = "Опиши что ты видишь на изображении подробно"
                    
            except Exception as e:
                logger.error(f"[IMAGE_ERROR] Ошибка обработки изображения: {e}")
                await message.reply_text("🚫 Ошибка при обработке изображения. Попробуйте еще раз.")
                return
        
        if not question_text:
            await message.reply_text(
                "❓ Пожалуйста, укажите ваш вопрос.\n\n"
                "*Пример:* `/ask Что такое искусственный интеллект?`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        
        # Эмуляция человеческого поведения для команды /ask
        try:
            await human_behavior_service.mark_as_read(chat.id)
        except Exception as e:
            logger.debug(f"[HUMAN_BEHAVIOR] Не удалось отметить сообщения как прочитанные: {e}")
        
        # Генерируем человеческую задержку для ответа
        human_delay = await human_behavior_service.simulate_human_delay(question_text)
        logger.info(f"🤖 Эмулируем человеческое поведение для команды /ask - задержка {human_delay/60:.1f} минут")
        
        # Анализируем сложность вопроса для тега человека  
        complexity_analysis = complexity_analyzer.analyze_complexity(question_text)
        should_tag_human = complexity_analysis["should_tag_human"]
        
        # Сохраняем сообщение пользователя в БД
        saved_message = None
        if db_manager:
            try:
                # Обновляем информацию о пользователе
                await db_manager.get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_admin=True
                )
                
                # Сохраняем сообщение
                saved_message = await db_manager.save_message(
                    telegram_message_id=message.message_id,
                    chat_id=chat.id,
                    user_id=user.id,
                    message_text=question_text,
                    message_type='photo' if image_data else 'text',
                    is_command=True,
                    command_name='ask',
                    has_image=bool(image_data)
                )
                
                logger.info(f"[DB] Сообщение сохранено в БД: {saved_message.id}")
            except Exception as e:
                logger.error(f"[DB_ERROR] Ошибка сохранения сообщения: {e}")
        
        # Логируем запрос
        logger.info(f"[ASK] Пользователь {user.id} задал вопрос: '{question_text[:100]}...'")
        if image_data:
            logger.info(f"[ASK] К вопросу прикреплено изображение")
        
        try:
            # Применяем человеческую задержку перед началом обработки
            await asyncio.sleep(human_delay)
            
            # Получаем ответ от GPT
            import time
            start_time = time.time()
            
            response_data = await self.gpt_service.get_response_async(
                message=question_text,
                image_data=image_data,
                chat_id=chat.id,
                model="auto"
            )
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            if response_data["success"]:
                response_text = response_data["response"]
                provider_used = response_data.get("provider_used", "unknown")
                model_used = response_data.get("model_used", "unknown")
                
                # Если вопрос сложный, добавляем тег пользователя
                if should_tag_human and config.HUMAN_TAG_USER_ID:
                    try:
                        human_user = await context.bot.get_chat(config.HUMAN_TAG_USER_ID)
                        human_mention = f"@{human_user.username}" if human_user.username else f"[Человек](tg://user?id={config.HUMAN_TAG_USER_ID})"
                        response_text = f"🧠 *Сложный вопрос для эксперта* {human_mention}\n\n{response_text}"
                    except Exception as e:
                        logger.error(f"[TAG_ERROR] Ошибка при теге человека: {e}")
                
                # Разбиваем длинные ответы на части
                message_parts = split_long_message(response_text, max_length=4000)
                
                # Отправляем ответ с эмуляцией человеческого поведения через Telethon
                for i, part in enumerate(message_parts):
                    try:
                        # Используем Telethon для эмуляции человеческого поведения
                        if human_behavior_service.is_initialized:
                            await human_behavior_service.send_message_with_human_behavior(
                                chat_id=chat.id,
                                message=part
                            )
                        else:
                            # Fallback на обычный Bot API
                            await message.reply_text(
                                part,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True
                            )
                    except Exception as send_error:
                        logger.error(f"[SEND_ERROR] Ошибка отправки через Telethon, используем fallback: {send_error}")
                        # Fallback на обычный telegram API
                        await message.reply_text(
                            part,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                
                # Обновляем сообщение в БД
                if db_manager and saved_message:
                    try:
                        await db_manager.update_message_response(
                            message_id=saved_message.id,
                            gpt_response=response_text,
                            model_used=model_used,
                            provider_used=provider_used,
                            response_time=response_time_ms
                        )
                        
                        # Логируем запрос
                        await db_manager.log_request(
                            user_id=user.id,
                            chat_id=chat.id,
                            request_type='ask',
                            input_length=len(question_text),
                            output_length=len(response_text),
                            response_time=response_time_ms,
                            success=True,
                            provider_used=provider_used,
                            model_used=model_used
                        )
                    except Exception as e:
                        logger.error(f"[DB_ERROR] Ошибка обновления ответа в БД: {e}")
                
                logger.info(f"[SUCCESS] Ответ отправлен пользователю {user.id}. Провайдер: {provider_used}, время: {format_duration(response_time_ms/1000)}")
                
            else:
                # Ошибка получения ответа
                error_text = response_data.get("response", "🚫 Не удалось получить ответ от AI.")
                await message.reply_text(error_text)
                
                # Логируем ошибку
                if db_manager:
                    try:
                        await db_manager.log_request(
                            user_id=user.id,
                            chat_id=chat.id,
                            request_type='ask',
                            input_length=len(question_text),
                            response_time=response_time_ms,
                            success=False,
                            error_message=response_data.get("error", "Unknown error")
                        )
                    except Exception as e:
                        logger.error(f"[DB_ERROR] Ошибка логирования неудачного запроса: {e}")
                
                logger.warning(f"[ERROR] Не удалось получить ответ для пользователя {user.id}: {response_data.get('error')}")
        
        except Exception as e:
            logger.error(f"[CRITICAL_ERROR] Критическая ошибка при обработке команды /ask: {e}")
            await message.reply_text(
                "🚫 Произошла критическая ошибка при обработке запроса. Попробуйте позже."
            )
            
            # Логируем критическую ошибку
            if db_manager:
                try:
                    await db_manager.log_request(
                        user_id=user.id,
                        chat_id=chat.id,
                        request_type='ask',
                        input_length=len(question_text),
                        success=False,
                        error_message=str(e)
                    )
                except Exception as db_e:
                    logger.error(f"[DB_ERROR] Ошибка логирования критической ошибки: {db_e}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        user = update.effective_user
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            return
        
        try:
            # Получаем информацию о провайдерах
            provider_info = self.gpt_service.get_provider_info()
            
            # Получаем статистику пользователя
            user_stats = rate_limiter.get_user_stats(user.id)
            
            # Получаем статистику из БД
            db_stats = None
            if db_manager:
                try:
                    db_stats = await db_manager.get_system_stats()
                except Exception as e:
                    logger.error(f"[DB_ERROR] Ошибка получения статистики из БД: {e}")
            
            status_text = f"""📊 *Статус системы*

*🤖 AI Провайдеры:*
• Текущий: `{provider_info['current']}`
• Рабочих: {provider_info['working_providers']}
• Резервных: {provider_info['backup_providers']}
• Vision: {provider_info['vision_providers']}

*⚡ Ваши лимиты:*
• Запросов за минуту: {user_stats['requests_in_window']}/{user_stats['max_requests']}
• Можно запросить: {'✅ Да' if user_stats['can_request_now'] else '❌ Нет'}
• Последний запрос: {format_duration(user_stats['last_request_ago']) + ' назад' if user_stats['last_request_ago'] else 'Нет данных'}"""

            if db_stats:
                status_text += f"""

*📈 Статистика системы:*
• Всего пользователей: {db_stats['total_users']}
• Активных (7 дней): {db_stats['active_users']}
• Всего сообщений: {db_stats['total_messages']}
• Сообщений сегодня: {db_stats['today_messages']}"""

            status_text += f"""

*⚙️ Конфигурация:*
• Лимит запросов: {config.MAX_REQUESTS_PER_MINUTE}/мин
• Макс. длина ответа: {config.MAX_MESSAGE_LENGTH} символов
• База данных: {'✅ Подключена' if db_manager else '❌ Отключена'}

_Обновлено: {time.strftime('%H:%M:%S')}_"""

            await update.message.reply_text(
                status_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            logger.info(f"[STATUS] Статус показан пользователю {user.id}")
            
        except Exception as e:
            logger.error(f"[ERROR] Ошибка получения статуса: {e}")
            await update.message.reply_text("🚫 Ошибка получения статуса системы.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats - персональная статистика пользователя"""
        user = update.effective_user
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            return
        
        try:
            # Получаем статистику из rate limiter
            rate_stats = rate_limiter.get_user_stats(user.id)
            
            # Получаем статистику из БД
            db_stats = None
            if db_manager:
                try:
                    db_stats = await db_manager.get_user_stats(user.id)
                except Exception as e:
                    logger.error(f"[DB_ERROR] Ошибка получения статистики пользователя: {e}")
            
            stats_text = f"""📊 *Ваша статистика*

*👤 Пользователь:* {user.first_name or user.username} (`{user.id}`)

*⚡ Текущая сессия:*
• Запросов за минуту: {rate_stats['requests_in_window']}/{rate_stats['max_requests']}
• Статус: {'🟢 Можно запросить' if rate_stats['can_request_now'] else '🔴 Ограничение активно'}
• Последний запрос: {format_duration(rate_stats['last_request_ago']) + ' назад' if rate_stats['last_request_ago'] else 'Нет данных'}"""

            if db_stats:
                stats_text += f"""

*📈 Общая статистика:*
• Всего сообщений: {db_stats['total_messages']}
• Команд выполнено: {db_stats['command_count']}
• Последняя активность: {db_stats['last_activity'].strftime('%d.%m.%Y %H:%M') if db_stats['last_activity'] else 'Нет данных'}"""

            stats_text += f"""

*🔧 Ваши права:*
• Администратор: ✅ Да
• Доступ к боту: ✅ Разрешен
• Доступ к /admin: ✅ Разрешен

_Статистика обновлена: {time.strftime('%H:%M:%S')}_"""

            await update.message.reply_text(
                stats_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            logger.info(f"[STATS] Статистика показана пользователю {user.id}")
            
        except Exception as e:
            logger.error(f"[ERROR] Ошибка получения статистики пользователя: {e}")
            await update.message.reply_text("🚫 Ошибка получения вашей статистики.")
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /admin - панель администратора"""
        user = update.effective_user
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            await update.message.reply_text("🚫 Доступ запрещен.")
            return
        
        try:
            # Получаем информацию о провайдерах
            provider_info = self.gpt_service.get_provider_info()
            provider_stats = provider_info.get('provider_stats', {})
            
            # Топ-3 провайдера по использованию
            top_providers = sorted(provider_stats.items(), key=lambda x: x[1], reverse=True)[:3]
            
            admin_text = f"""🔧 *Панель администратора*

*🤖 AI Провайдеры:*
• Текущий активный: `{provider_info['current']}`
• Всего доступно: {len(provider_info['all'])}
• Рабочих: {provider_info['working_providers']}
• Резервных: {provider_info['backup_providers']}
• Vision: {provider_info['vision_providers']}

*📊 Топ провайдеры:*"""

            for i, (provider, count) in enumerate(top_providers, 1):
                admin_text += f"\n{i}. `{provider}` - {count} запросов"
            
            if not top_providers:
                admin_text += "\n_Статистика пока не собрана_"

            # Информация о системе
            if db_manager:
                try:
                    system_stats = await db_manager.get_system_stats()
                    admin_text += f"""

*📈 Система:*
• Всего пользователей: {system_stats['total_users']}
• Активных (7 дней): {system_stats['active_users']}
• Всего сообщений: {system_stats['total_messages']}
• Сообщений сегодня: {system_stats['today_messages']}"""
                except Exception as e:
                    logger.error(f"[DB_ERROR] Ошибка получения системной статистики: {e}")
                    admin_text += "\n\n*📈 Система:* ❌ Ошибка получения данных"

            admin_text += f"""

*⚙️ Конфигурация:*
• Администраторов: {len(config.TELEGRAM_ADMIN_IDS)}
• Лимит запросов: {config.MAX_REQUESTS_PER_MINUTE}/мин
• Макс. длина: {config.MAX_MESSAGE_LENGTH} символов

*🔧 Доступные команды:*
• `/reset [user_id]` - Сбросить лимиты пользователя
• `/providers` - Детальная информация о провайдерах

_Панель обновлена: {time.strftime('%H:%M:%S')}_"""

            await update.message.reply_text(
                admin_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            logger.info(f"[ADMIN] Панель администратора показана пользователю {user.id}")
            
        except Exception as e:
            logger.error(f"[ERROR] Ошибка показа панели администратора: {e}")
            await update.message.reply_text("🚫 Ошибка получения данных панели администратора.")
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /reset - сброс лимитов пользователя"""
        user = update.effective_user
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            return
        
        # Проверяем аргументы
        if not context.args:
            await update.message.reply_text(
                "❓ Укажите ID пользователя.\n\n*Пример:* `/reset 123456789`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            
            # Сбрасываем лимиты
            rate_limiter.reset_user(target_user_id)
            
            await update.message.reply_text(
                f"✅ Лимиты пользователя `{target_user_id}` сброшены.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"[RESET] Администратор {user.id} сбросил лимиты пользователя {target_user_id}")
            
        except ValueError:
            await update.message.reply_text("❌ Неверный формат ID пользователя.")
        except Exception as e:
            logger.error(f"[ERROR] Ошибка сброса лимитов: {e}")
            await update.message.reply_text("🚫 Ошибка при сбросе лимитов.")
    
    async def providers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /providers - детальная информация о провайдерах"""
        user = update.effective_user
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            return
        
        try:
            provider_info = self.gpt_service.get_provider_info()
            
            providers_text = f"""🤖 *Детальная информация о AI провайдерах*

*📊 Общая статистика:*
• Текущий провайдер: `{provider_info['current']}`
• Всего провайдеров: {len(provider_info['all'])}
• Рабочих: {provider_info['working_providers']}
• Резервных: {provider_info['backup_providers']}
• Vision: {provider_info['vision_providers']}

*⚡ Быстрые провайдеры (до 3с):*"""
            
            for provider in self.gpt_service.fast_providers:
                status = "🟢" if provider == provider_info['current'] else "⚪"
                usage = provider_info['provider_stats'].get(provider, 0)
                providers_text += f"\n{status} `{provider}` - {usage} использований"
            
            providers_text += "\n\n*🔶 Средние провайдеры (3-6с):*"
            for provider in self.gpt_service.medium_providers:
                status = "🟢" if provider == provider_info['current'] else "⚪"
                usage = provider_info['provider_stats'].get(provider, 0)
                providers_text += f"\n{status} `{provider}` - {usage} использований"
            
            providers_text += "\n\n*🟠 Медленные провайдеры (6с+):*"
            for provider in self.gpt_service.slow_providers:
                status = "🟢" if provider == provider_info['current'] else "⚪"
                usage = provider_info['provider_stats'].get(provider, 0)
                providers_text += f"\n{status} `{provider}` - {usage} использований"
            
            providers_text += "\n\n*👁️ Vision провайдеры:*"
            for provider in self.gpt_service.vision_providers:
                status = "🟢" if provider == provider_info['current'] else "⚪"
                usage = provider_info['provider_stats'].get(provider, 0)
                providers_text += f"\n{status} `{provider}` - {usage} использований"
            
            providers_text += f"\n\n_Обновлено: {time.strftime('%H:%M:%S')}_"
            
            # Разбиваем на части если слишком длинное
            message_parts = split_long_message(providers_text, max_length=4000)
            
            for part in message_parts:
                await update.message.reply_text(
                    part,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            
            logger.info(f"[PROVIDERS] Информация о провайдерах показана пользователю {user.id}")
            
        except Exception as e:
            logger.error(f"[ERROR] Ошибка получения информации о провайдерах: {e}")
            await update.message.reply_text("🚫 Ошибка получения информации о провайдерах.")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на инлайн-кнопки"""
        query = update.callback_query
        user = query.from_user
        
        # Отвечаем на callback query
        await query.answer()
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            await query.edit_message_text("🚫 Доступ запрещен.")
            return
        
        action = query.data
        
        if action == "action_ask":
            # Режим вопроса - показываем инструкцию
            keyboard = [
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            instruction_text = """❓ *Режим вопросов активирован*

🖊️ **Как задать вопрос:**
• Просто напишите ваш вопрос текстом
• Отправьте изображение с подписью-вопросом
• Я отвечу на любые вопросы!

💡 **Примеры:**
• "Что такое искусственный интеллект?"
• "Напиши код на Python"
• [Фото] "Что на этом изображении?"

_Ожидаю ваш вопрос..._"""
            
            await query.edit_message_text(
                instruction_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            # Устанавливаем режим ожидания вопроса
            context.user_data['waiting_for_question'] = True
            
        elif action == "action_status":
            # Показываем статус
            await self._show_status_inline(query, context)
            
        elif action == "action_stats":
            # Показываем статистику пользователя
            await self._show_stats_inline(query, context)
            
        elif action == "action_admin":
            # Показываем админ панель
            await self._show_admin_inline(query, context)
            
        elif action == "action_providers":
            # Показываем провайдеры
            await self._show_providers_inline(query, context)
            
        elif action == "action_help":
            # Показываем справку
            await self._show_help_inline(query, context)
            
        elif action == "action_menu":
            # Возврат в главное меню
            await self._show_main_menu(query, context)
    
    async def _show_main_menu(self, query, context):
        """Показать главное меню"""
        user = query.from_user
        
        menu_text = f"""🤖 *AI Ассистент*

Добро пожаловать, {user.first_name or user.username}!
Выберите действие:"""

        keyboard = [
            [
                InlineKeyboardButton("❓ Задать вопрос", callback_data="action_ask"),
                InlineKeyboardButton("📊 Статус", callback_data="action_status")
            ],
            [
                InlineKeyboardButton("📈 Моя статистика", callback_data="action_stats"),
                InlineKeyboardButton("🔧 Админ панель", callback_data="action_admin")
            ],
            [
                InlineKeyboardButton("🤖 Провайдеры", callback_data="action_providers"),
                InlineKeyboardButton("ℹ️ Справка", callback_data="action_help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            menu_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _show_status_inline(self, query, context):
        """Показать статус в инлайн режиме"""
        try:
            provider_info = self.gpt_service.get_provider_info()
            user_stats = rate_limiter.get_user_stats(query.from_user.id)
            
            status_text = f"""📊 *Статус системы*

*🤖 AI Провайдеры:*
• Текущий: `{provider_info['current']}`
• Рабочих: {provider_info['working_providers']}
• Резервных: {provider_info['backup_providers']}
• Vision: {provider_info['vision_providers']}

*⚡ Ваши лимиты:*
• Запросов за минуту: {user_stats['requests_in_window']}/{user_stats['max_requests']}
• Можно запросить: {'✅ Да' if user_stats['can_request_now'] else '❌ Нет'}

*⚙️ Конфигурация:*
• Лимит запросов: {config.MAX_REQUESTS_PER_MINUTE}/мин
• База данных: {'✅ Подключена' if db_manager else '❌ Отключена'}"""

            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                status_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"[ERROR] Ошибка показа статуса: {e}")
            await query.edit_message_text("🚫 Ошибка получения статуса.")
    
    async def _show_stats_inline(self, query, context):
        """Показать статистику пользователя в инлайн режиме"""
        try:
            user = query.from_user
            rate_stats = rate_limiter.get_user_stats(user.id)
            
            db_stats = None
            if db_manager:
                try:
                    db_stats = await db_manager.get_user_stats(user.id)
                except Exception as e:
                    logger.error(f"[DB_ERROR] Ошибка получения статистики: {e}")
            
            stats_text = f"""📊 *Ваша статистика*

*👤 Пользователь:* {user.first_name or user.username}

*⚡ Текущая сессия:*
• Запросов за минуту: {rate_stats['requests_in_window']}/{rate_stats['max_requests']}
• Статус: {'🟢 Можно запросить' if rate_stats['can_request_now'] else '🔴 Ограничение активно'}"""

            if db_stats:
                stats_text += f"""

*📈 Общая статистика:*
• Всего сообщений: {db_stats['total_messages']}
• Команд выполнено: {db_stats['command_count']}"""

            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                stats_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"[ERROR] Ошибка показа статистики: {e}")
            await query.edit_message_text("🚫 Ошибка получения статистики.")
    
    async def _show_admin_inline(self, query, context):
        """Показать админ панель в инлайн режиме"""
        try:
            provider_info = self.gpt_service.get_provider_info()
            provider_stats = provider_info.get('provider_stats', {})
            
            top_providers = sorted(provider_stats.items(), key=lambda x: x[1], reverse=True)[:2]
            
            admin_text = f"""🔧 *Админ панель*

*🤖 AI Провайдеры:*
• Текущий: `{provider_info['current']}`
• Всего: {len(provider_info['all'])}
• Рабочих: {provider_info['working_providers']}"""

            if top_providers:
                admin_text += "\n\n*📊 Топ провайдеры:*"
                for i, (provider, count) in enumerate(top_providers, 1):
                    admin_text += f"\n{i}. `{provider}` - {count}"

            if db_manager:
                try:
                    system_stats = await db_manager.get_system_stats()
                    admin_text += f"""

*📈 Система:*
• Пользователей: {system_stats['total_users']}
• Сообщений: {system_stats['total_messages']}"""
                except Exception:
                    pass

            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                admin_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"[ERROR] Ошибка показа админ панели: {e}")
            await query.edit_message_text("🚫 Ошибка получения данных.")
    
    async def _show_providers_inline(self, query, context):
        """Показать провайдеры в инлайн режиме"""
        try:
            provider_info = self.gpt_service.get_provider_info()
            
            providers_text = f"""🤖 *AI Провайдеры*

*📊 Статистика:*
• Текущий: `{provider_info['current']}`
• Всего: {len(provider_info['all'])}
• Рабочих: {provider_info['working_providers']}
• Vision: {provider_info['vision_providers']}

*⚡ Быстрые:* {len(self.gpt_service.fast_providers)}
*🔶 Средние:* {len(self.gpt_service.medium_providers)}
*🟠 Медленные:* {len(self.gpt_service.slow_providers)}"""

            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                providers_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"[ERROR] Ошибка показа провайдеров: {e}")
            await query.edit_message_text("🚫 Ошибка получения информации.")
    
    async def _show_help_inline(self, query, context):
        """Показать справку в инлайн режиме"""
        help_text = """ℹ️ *Справка по AI ассистенту*

*🎯 Основные возможности:*
• Ответы на любые вопросы
• Анализ изображений
• Помощь с программированием
• Объяснение сложных тем

*🖼️ Работа с изображениями:*
Отправьте фото с вопросом в подписи

*⚡ Ограничения:*
• {config.MAX_REQUESTS_PER_MINUTE} запросов в минуту
• История разговоров сохраняется

*🔧 Для администраторов:*
Полный доступ ко всем функциям бота""".format(config=config)

        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик обычных сообщений (не команд)"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Проверяем права доступа
        if user.id not in config.TELEGRAM_ADMIN_IDS:
            return
        
        # В личных сообщениях отвечаем сразу на любые сообщения
        if chat.type == 'private':
            waiting_for_question = context.user_data.get('waiting_for_question', False)
            
            if waiting_for_question:
                # Если активирован режим ожидания - используем эмуляцию человека
                await self._process_ai_question(update, context, use_human_behavior=True)
                context.user_data['waiting_for_question'] = False
            else:
                # Обычные сообщения - тоже с эмуляцией человеческого поведения
                await self._process_simple_message(update, context)
        else:
            # В группах работаем по старой схеме с кнопками
            keyboard = [
                [InlineKeyboardButton("❓ Задать вопрос", callback_data="action_ask")],
                [InlineKeyboardButton("📊 Меню", callback_data="action_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                "💡 Для взаимодействия используйте кнопки:",
                reply_markup=reply_markup
            )
    
    async def _process_simple_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка простого сообщения с эмуляцией человеческого поведения"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Проверяем rate limiting
        is_allowed, error_msg = rate_limiter.is_allowed(
            user.id, 
            max_requests=config.MAX_REQUESTS_PER_MINUTE,
            time_window=60
        )
        
        if not is_allowed:
            await message.reply_text(f"⏱️ {error_msg}")
            logger.warning(f"[RATE_LIMIT] Пользователь {user.id} превысил лимит: {error_msg}")
            return
        
        # Извлекаем текст сообщения
        question_text = message.text or ""
        
        # Анализируем сложность вопроса
        complexity_analysis = complexity_analyzer.analyze_complexity(question_text)
        should_tag_human = complexity_analysis["should_tag_human"]
        
        logger.info(f"[SIMPLE_MSG] Пользователь {user.id}: '{question_text[:50]}...' (сложность: {complexity_analysis['complexity_level']})")
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        
        # Эмуляция человеческого поведения для всех сообщений
        try:
            await human_behavior_service.mark_as_read(chat.id)
        except Exception as e:
            logger.debug(f"[HUMAN_BEHAVIOR] Не удалось отметить сообщения как прочитанные: {e}")
        
        # Генерируем человеческую задержку для ответа
        human_delay = await human_behavior_service.simulate_human_delay(question_text)
        logger.info(f"🤖 Эмулируем человеческое поведение для простого сообщения - задержка {human_delay/60:.1f} минут")
        
        try:
            # Применяем человеческую задержку перед началом обработки
            await asyncio.sleep(human_delay)
            
            # Получаем ответ от GPT
            import time
            start_time = time.time()
            
            response_data = await self.gpt_service.get_response_async(
                message=question_text,
                image_data=None,
                chat_id=chat.id,
                model="auto"
            )
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            if response_data["success"]:
                response_text = response_data["response"]
                provider_used = response_data.get("provider_used", "unknown")
                model_used = response_data.get("model_used", "unknown")
                
                # Если вопрос сложный, добавляем тег пользователя
                if should_tag_human and config.HUMAN_TAG_USER_ID:
                    try:
                        human_user = await context.bot.get_chat(config.HUMAN_TAG_USER_ID)
                        human_mention = f"@{human_user.username}" if human_user.username else f"[Человек](tg://user?id={config.HUMAN_TAG_USER_ID})"
                        response_text = f"🧠 *Сложный вопрос для эксперта* {human_mention}\n\n{response_text}"
                    except Exception as e:
                        logger.error(f"[TAG_ERROR] Ошибка при теге человека: {e}")
                
                # Разбиваем длинные ответы на части
                message_parts = split_long_message(response_text, max_length=4000)
                
                # Отправляем ответ с эмуляцией человеческого поведения через Telethon
                for i, part in enumerate(message_parts):
                    try:
                        # Используем Telethon для более человечного поведения
                        if human_behavior_service.is_initialized and chat.type == 'private':
                            # Отправляем через Telethon с человеческим поведением
                            await human_behavior_service.send_message_with_human_behavior(
                                chat_id=chat.id,
                                message=part
                            )
                        else:
                            # Fallback на обычный API
                            await message.reply_text(
                                part,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True
                            )
                    except Exception as send_error:
                        logger.error(f"[SEND_ERROR] Ошибка отправки через Telethon, используем fallback: {send_error}")
                        # Fallback на обычный telegram API
                        await message.reply_text(
                            part,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                
                logger.info(f"[SIMPLE_SUCCESS] Ответ отправлен пользователю {user.id}. Провайдер: {provider_used}, сложность: {complexity_analysis['complexity_level']}")
                
            else:
                # Ошибка получения ответа
                error_text = response_data.get("response", "🚫 Не удалось получить ответ от AI.")
                await message.reply_text(error_text)
                logger.warning(f"[SIMPLE_ERROR] Не удалось получить ответ для пользователя {user.id}: {response_data.get('error')}")
        
        except Exception as e:
            logger.error(f"[SIMPLE_CRITICAL] Критическая ошибка при обработке простого сообщения: {e}")
            await message.reply_text("🚫 Произошла ошибка при обработке запроса. Попробуйте позже.")
    
    async def _process_ai_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, use_human_behavior: bool = False):
        """Обработка вопроса к AI (вынесено из ask_command)"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Проверяем rate limiting
        is_allowed, error_msg = rate_limiter.is_allowed(
            user.id, 
            max_requests=config.MAX_REQUESTS_PER_MINUTE,
            time_window=60
        )
        
        if not is_allowed:
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                f"⏱️ {error_msg}",
                reply_markup=reply_markup
            )
            logger.warning(f"[RATE_LIMIT] Пользователь {user.id} превысил лимит: {error_msg}")
            return
        
        # Извлекаем текст вопроса
        question_text = message.text or ""
        
        # Проверяем наличие изображения
        image_data = None
        if message.photo:
            try:
                # Получаем изображение наибольшего размера
                photo = message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                
                # Скачиваем изображение
                import io
                import base64
                
                image_bytes = io.BytesIO()
                await file.download_to_memory(image_bytes)
                image_bytes.seek(0)
                
                # Конвертируем в base64
                image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
                image_data = f"data:image/jpeg;base64,{image_base64}"
                
                logger.info(f"[IMAGE] Получено изображение от пользователя {user.id}")
                
                if not question_text:
                    question_text = "Опиши что ты видишь на изображении подробно"
                    
            except Exception as e:
                logger.error(f"[IMAGE_ERROR] Ошибка обработки изображения: {e}")
                await message.reply_text("🚫 Ошибка при обработке изображения. Попробуйте еще раз.")
                return
        
        if not question_text:
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                "❓ Пожалуйста, укажите ваш вопрос или отправьте изображение с подписью.",
                reply_markup=reply_markup
            )
            return
        
        # Показываем, что бот печатает
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        
        # Эмуляция человеческого поведения только если требуется
        human_delay = 0
        if use_human_behavior:
            # Эмуляция человеческого поведения - отмечаем сообщения как прочитанные
            try:
                await human_behavior_service.mark_as_read(chat.id)
            except Exception as e:
                logger.debug(f"[HUMAN_BEHAVIOR] Не удалось отметить сообщения как прочитанные: {e}")
            
            # Генерируем человеческую задержку для ответа
            human_delay = await human_behavior_service.simulate_human_delay(question_text)
            logger.info(f"🤖 Эмулируем человеческое поведение - задержка {human_delay/60:.1f} минут")
        
        # Анализируем сложность вопроса для тега человека
        complexity_analysis = complexity_analyzer.analyze_complexity(question_text)
        should_tag_human = complexity_analysis["should_tag_human"]
        
        # Сохраняем сообщение пользователя в БД
        saved_message = None
        if db_manager:
            try:
                # Обновляем информацию о пользователе
                await db_manager.get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_admin=True
                )
                
                # Сохраняем сообщение
                saved_message = await db_manager.save_message(
                    telegram_message_id=message.message_id,
                    chat_id=chat.id,
                    user_id=user.id,
                    message_text=question_text,
                    message_type='photo' if image_data else 'text',
                    is_command=False,  # Это обычное сообщение, не команда
                    command_name='ask_button',
                    has_image=bool(image_data)
                )
                
                logger.info(f"[DB] Сообщение сохранено в БД: {saved_message.id}")
            except Exception as e:
                logger.error(f"[DB_ERROR] Ошибка сохранения сообщения: {e}")
        
        # Логируем запрос
        logger.info(f"[ASK_BUTTON] Пользователь {user.id} задал вопрос: '{question_text[:100]}...'")
        if image_data:
            logger.info(f"[ASK_BUTTON] К вопросу прикреплено изображение")
        
        try:
            # Применяем человеческую задержку перед началом обработки только если требуется
            if use_human_behavior and human_delay > 0:
                await asyncio.sleep(human_delay)
            
            # Получаем ответ от GPT
            import time
            start_time = time.time()
            
            response_data = await self.gpt_service.get_response_async(
                message=question_text,
                image_data=image_data,
                chat_id=chat.id,
                model="auto"
            )
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            if response_data["success"]:
                response_text = response_data["response"]
                provider_used = response_data.get("provider_used", "unknown")
                model_used = response_data.get("model_used", "unknown")
                
                # Разбиваем длинные ответы на части
                message_parts = split_long_message(response_text, max_length=4000)
                
                # Отправляем ответ с эмуляцией человеческого поведения
                for i, part in enumerate(message_parts):
                    try:
                        # Используем Telethon для более человечного поведения
                        if human_behavior_service.is_initialized and chat.type == 'private':
                            if i == len(message_parts) - 1:  # Последняя часть
                                # Добавляем кнопку в последнее сообщение через обычный API
                                keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
                                reply_markup = InlineKeyboardMarkup(keyboard)
                                
                                await message.reply_text(
                                    part,
                                    parse_mode=ParseMode.MARKDOWN,
                                    disable_web_page_preview=True,
                                    reply_markup=reply_markup
                                )
                            else:
                                # Отправляем через Telethon с человеческим поведением
                                await human_behavior_service.send_message_with_human_behavior(
                                    chat_id=chat.id,
                                    message=part
                                )
                        else:
                            # Fallback на обычный API
                            if i == len(message_parts) - 1:  # Последняя часть - добавляем кнопку меню
                                keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
                                reply_markup = InlineKeyboardMarkup(keyboard)
                                
                                await message.reply_text(
                                    part,
                                    parse_mode=ParseMode.MARKDOWN,
                                    disable_web_page_preview=True,
                                    reply_markup=reply_markup
                                )
                            else:
                                await message.reply_text(
                                    part,
                                    parse_mode=ParseMode.MARKDOWN,
                                    disable_web_page_preview=True
                                )
                    except Exception as send_error:
                        logger.error(f"[SEND_ERROR] Ошибка отправки через Telethon, используем fallback: {send_error}")
                        # Fallback на обычный telegram API
                        if i == len(message_parts) - 1:  # Последняя часть - добавляем кнопку меню
                            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            
                            await message.reply_text(
                                part,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True,
                                reply_markup=reply_markup
                            )
                        else:
                            await message.reply_text(
                                part,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True
                            )
                
                # Обновляем сообщение в БД
                if db_manager and saved_message:
                    try:
                        await db_manager.update_message_response(
                            message_id=saved_message.id,
                            gpt_response=response_text,
                            model_used=model_used,
                            provider_used=provider_used,
                            response_time=response_time_ms
                        )
                        
                        # Логируем запрос
                        await db_manager.log_request(
                            user_id=user.id,
                            chat_id=chat.id,
                            request_type='ask_button',
                            input_length=len(question_text),
                            output_length=len(response_text),
                            response_time=response_time_ms,
                            success=True,
                            provider_used=provider_used,
                            model_used=model_used
                        )
                    except Exception as e:
                        logger.error(f"[DB_ERROR] Ошибка обновления ответа в БД: {e}")
                
                logger.info(f"[SUCCESS] Ответ отправлен пользователю {user.id}. Провайдер: {provider_used}, время: {format_duration(response_time_ms/1000)}")
                
            else:
                # Ошибка получения ответа
                error_text = response_data.get("response", "🚫 Не удалось получить ответ от AI.")
                
                keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await message.reply_text(error_text, reply_markup=reply_markup)
                
                # Логируем ошибку
                if db_manager:
                    try:
                        await db_manager.log_request(
                            user_id=user.id,
                            chat_id=chat.id,
                            request_type='ask_button',
                            input_length=len(question_text),
                            response_time=response_time_ms,
                            success=False,
                            error_message=response_data.get("error", "Unknown error")
                        )
                    except Exception as e:
                        logger.error(f"[DB_ERROR] Ошибка логирования неудачного запроса: {e}")
                
                logger.warning(f"[ERROR] Не удалось получить ответ для пользователя {user.id}: {response_data.get('error')}")
        
        except Exception as e:
            logger.error(f"[CRITICAL_ERROR] Критическая ошибка при обработке вопроса: {e}")
            
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="action_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                "🚫 Произошла критическая ошибка при обработке запроса. Попробуйте позже.",
                reply_markup=reply_markup
            )
            
            # Логируем критическую ошибку
            if db_manager:
                try:
                    await db_manager.log_request(
                        user_id=user.id,
                        chat_id=chat.id,
                        request_type='ask_button',
                        input_length=len(question_text),
                        success=False,
                        error_message=str(e)
                    )
                except Exception as db_e:
                    logger.error(f"[DB_ERROR] Ошибка логирования критической ошибки: {db_e}")

# Глобальный экземпляр обработчиков команд
command_handlers = CommandHandlers()
