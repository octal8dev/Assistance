"""
Менеджер базы данных для телеграм бота
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, desc, and_, or_
from .models import Base, User, Chat, Message, RequestLog

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self, database_url: str):
        # Преобразуем URL для асинхронного подключения
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Отключаем вывод SQL запросов
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_db(self):
        """Инициализация базы данных"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ База данных инициализирована успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    async def close(self):
        """Закрытие соединения с БД"""
        await self.engine.dispose()
        logger.info("🔌 Соединение с БД закрыто")
    
    # === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===
    
    async def get_or_create_user(self, telegram_id: int, username: str = None, 
                                first_name: str = None, last_name: str = None,
                                is_admin: bool = False) -> User:
        """Получить или создать пользователя"""
        async with self.async_session() as session:
            # Попытка найти существующего пользователя
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Обновляем информацию о пользователе
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.last_activity = datetime.utcnow()
                if is_admin:
                    user.is_admin = True
            else:
                # Создаем нового пользователя
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=is_admin,
                    last_activity=datetime.utcnow()
                )
                session.add(user)
            
            await session.commit()
            await session.refresh(user)
            return user
    
    async def is_user_admin(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User.is_admin).where(
                    and_(User.telegram_id == telegram_id, User.is_active == True)
                )
            )
            is_admin = result.scalar_one_or_none()
            return bool(is_admin)
    
    async def update_user_activity(self, telegram_id: int):
        """Обновить время последней активности пользователя"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.last_activity = datetime.utcnow()
                await session.commit()
    
    # === УПРАВЛЕНИЕ ЧАТАМИ ===
    
    async def get_or_create_chat(self, chat_id: int, chat_type: str, title: str = None) -> Chat:
        """Получить или создать чат"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Chat).where(Chat.chat_id == chat_id)
            )
            chat = result.scalar_one_or_none()
            
            if chat:
                # Обновляем информацию о чате
                chat.title = title
                chat.updated_at = datetime.utcnow()
            else:
                # Создаем новый чат
                chat = Chat(
                    chat_id=chat_id,
                    chat_type=chat_type,
                    title=title
                )
                session.add(chat)
            
            await session.commit()
            await session.refresh(chat)
            return chat
    
    # === УПРАВЛЕНИЕ СООБЩЕНИЯМИ ===
    
    async def save_message(self, telegram_message_id: int, chat_id: int, user_id: int,
                          message_text: str = None, message_type: str = 'text',
                          is_command: bool = False, command_name: str = None,
                          has_image: bool = False) -> Message:
        """Сохранить сообщение пользователя"""
        async with self.async_session() as session:
            message = Message(
                telegram_message_id=telegram_message_id,
                chat_id=chat_id,
                user_id=user_id,
                message_text=message_text,
                message_type=message_type,
                is_command=is_command,
                command_name=command_name,
                has_image=has_image
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message
    
    async def update_message_response(self, message_id: int, gpt_response: str,
                                    model_used: str = None, provider_used: str = None,
                                    response_time: int = None):
        """Обновить сообщение с ответом GPT"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Message).where(Message.id == message_id)
            )
            message = result.scalar_one_or_none()
            
            if message:
                message.gpt_response = gpt_response
                message.gpt_model_used = model_used
                message.gpt_provider_used = provider_used
                message.gpt_response_time = response_time
                message.processed_at = datetime.utcnow()
                await session.commit()
    
    async def get_chat_history(self, chat_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить историю сообщений чата"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(desc(Message.created_at))
                .limit(limit)
            )
            messages = result.scalars().all()
            
            # Преобразуем в список словарей (в обратном порядке - от старых к новым)
            history = []
            for message in reversed(messages):
                if message.message_text:  # Сообщение пользователя
                    history.append({
                        "message_type": "user",
                        "message": message.message_text,
                        "created_at": message.created_at
                    })
                
                if message.gpt_response:  # Ответ бота
                    history.append({
                        "message_type": "assistant", 
                        "response": message.gpt_response,
                        "created_at": message.processed_at or message.created_at
                    })
            
            return history
    
    # === ЛОГИРОВАНИЕ ЗАПРОСОВ ===
    
    async def log_request(self, user_id: int, chat_id: int, request_type: str,
                         input_length: int = None, output_length: int = None,
                         response_time: int = None, success: bool = True,
                         error_message: str = None, provider_used: str = None,
                         model_used: str = None) -> RequestLog:
        """Логировать запрос"""
        async with self.async_session() as session:
            log_entry = RequestLog(
                user_id=user_id,
                chat_id=chat_id,
                request_type=request_type,
                input_length=input_length,
                output_length=output_length,
                response_time=response_time,
                success=success,
                error_message=error_message,
                provider_used=provider_used,
                model_used=model_used
            )
            session.add(log_entry)
            await session.commit()
            await session.refresh(log_entry)
            return log_entry
    
    async def check_rate_limit(self, user_id: int, max_requests: int = 10, 
                              time_window_minutes: int = 1) -> tuple[bool, int]:
        """
        Проверить ограничение частоты запросов
        Возвращает (разрешен_ли_запрос, количество_запросов_за_период)
        """
        async with self.async_session() as session:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            result = await session.execute(
                select(func.count(RequestLog.id))
                .where(
                    and_(
                        RequestLog.user_id == user_id,
                        RequestLog.created_at > cutoff_time
                    )
                )
            )
            request_count = result.scalar() or 0
            
            return request_count < max_requests, request_count
    
    # === СТАТИСТИКА ===
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        async with self.async_session() as session:
            # Общее количество сообщений
            total_messages = await session.execute(
                select(func.count(Message.id)).where(Message.user_id == user_id)
            )
            
            # Количество команд
            command_count = await session.execute(
                select(func.count(Message.id)).where(
                    and_(Message.user_id == user_id, Message.is_command == True)
                )
            )
            
            # Последняя активность
            last_activity = await session.execute(
                select(User.last_activity).where(User.telegram_id == user_id)
            )
            
            return {
                "total_messages": total_messages.scalar() or 0,
                "command_count": command_count.scalar() or 0,
                "last_activity": last_activity.scalar()
            }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Получить общую статистику системы"""
        async with self.async_session() as session:
            # Всего пользователей
            total_users = await session.execute(select(func.count(User.id)))
            
            # Активных пользователей (за последние 7 дней)
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_users = await session.execute(
                select(func.count(User.id)).where(User.last_activity > week_ago)
            )
            
            # Всего сообщений
            total_messages = await session.execute(select(func.count(Message.id)))
            
            # Сообщений за сегодня
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_messages = await session.execute(
                select(func.count(Message.id)).where(Message.created_at > today)
            )
            
            return {
                "total_users": total_users.scalar() or 0,
                "active_users": active_users.scalar() or 0,
                "total_messages": total_messages.scalar() or 0,
                "today_messages": today_messages.scalar() or 0
            }

# Глобальный экземпляр менеджера БД (будет инициализирован позже)
db_manager: Optional[DatabaseManager] = None

async def init_database(database_url: str) -> DatabaseManager:
    """Инициализация менеджера базы данных"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    await db_manager.init_db()
    return db_manager

async def close_database():
    """Закрытие соединения с базой данных"""
    if db_manager:
        await db_manager.close()
