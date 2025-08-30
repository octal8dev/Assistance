"""
Модели базы данных для телеграм бота
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_activity = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"

class Chat(Base):
    """Модель чата"""
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    chat_type = Column(String(50), nullable=False)  # 'private', 'group', 'supergroup', 'channel'
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Chat(chat_id={self.chat_id}, type={self.chat_type})>"

class Message(Base):
    """Модель сообщения"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_message_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    
    # Контент сообщения
    message_text = Column(Text, nullable=True)
    message_type = Column(String(50), default='text', nullable=False)  # 'text', 'photo', 'document', etc.
    
    # GPT ответ
    gpt_response = Column(Text, nullable=True)
    gpt_model_used = Column(String(100), nullable=True)
    gpt_provider_used = Column(String(100), nullable=True)
    gpt_response_time = Column(Integer, nullable=True)  # в миллисекундах
    
    # Метаданные
    is_command = Column(Boolean, default=False, nullable=False)
    command_name = Column(String(50), nullable=True)
    has_image = Column(Boolean, default=False, nullable=False)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Индексы для быстрого поиска
    __table_args__ = (
        Index('ix_messages_chat_created', 'chat_id', 'created_at'),
        Index('ix_messages_user_created', 'user_id', 'created_at'),
        Index('ix_messages_command', 'is_command', 'command_name'),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, user_id={self.user_id})>"

class RequestLog(Base):
    """Лог запросов для мониторинга и ограничения частоты"""
    __tablename__ = 'request_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    request_type = Column(String(50), nullable=False)  # 'ask', 'image', etc.
    
    # Детали запроса
    input_length = Column(Integer, nullable=True)
    output_length = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # в миллисекундах
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Технические детали
    provider_used = Column(String(100), nullable=True)
    model_used = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Индекс для rate limiting
    __table_args__ = (
        Index('ix_request_logs_user_time', 'user_id', 'created_at'),
        Index('ix_request_logs_chat_time', 'chat_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<RequestLog(user_id={self.user_id}, type={self.request_type}, success={self.success})>"
