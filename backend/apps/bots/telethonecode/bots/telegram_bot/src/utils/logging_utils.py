"""
Утилиты для работы с логированием
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Настройка системы логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_file: Путь к файлу логов (опционально)
    
    Returns:
        Настроенный логгер
    """
    # Определяем уровень логирования
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Создаем форматтер
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Удаляем существующие handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Файловый handler (если указан файл)
    if log_file:
        # Создаем директорию для логов если её нет
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Отключаем логи от некоторых библиотек
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)
    
    logger = logging.getLogger('telegram_bot')
    logger.info(f"🔧 Логирование настроено. Уровень: {log_level}")
    if log_file:
        logger.info(f"📝 Логи сохраняются в файл: {log_file}")
    
    return logger

def escape_markdown(text: str) -> str:
    """
    Экранирование специальных символов для Telegram MarkdownV2
    
    Args:
        text: Исходный текст
        
    Returns:
        Экранированный текст
    """
    # Символы, которые нужно экранировать в MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_duration(seconds: float) -> str:
    """
    Форматирование времени в читаемый вид
    
    Args:
        seconds: Время в секундах
        
    Returns:
        Отформатированная строка времени
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}мс"
    elif seconds < 60:
        return f"{seconds:.1f}с"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}м {secs}с"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}ч {minutes}м"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезание текста до указанной длины
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_user_mention(user_id: int, first_name: str = None, username: str = None) -> str:
    """
    Создание упоминания пользователя
    
    Args:
        user_id: ID пользователя в Telegram
        first_name: Имя пользователя
        username: Username пользователя
        
    Returns:
        Отформатированное упоминание
    """
    if username:
        return f"@{username}"
    elif first_name:
        return f"[{first_name}](tg://user?id={user_id})"
    else:
        return f"[Пользователь](tg://user?id={user_id})"

def validate_admin_id(admin_id_str: str) -> bool:
    """
    Валидация ID администратора
    
    Args:
        admin_id_str: ID администратора в виде строки
        
    Returns:
        True если ID валиден
    """
    try:
        admin_id = int(admin_id_str.strip())
        # Telegram user ID должен быть положительным числом
        return admin_id > 0
    except (ValueError, AttributeError):
        return False

def split_long_message(text: str, max_length: int = 4000) -> list:
    """
    Разбиение длинного сообщения на части
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина одной части
        
    Returns:
        Список частей сообщения
    """
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разбиваем по строкам
    lines = text.split('\n')
    
    for line in lines:
        # Если добавление строки превышает лимит
        if len(current_part) + len(line) + 1 > max_length:
            if current_part:
                parts.append(current_part.strip())
                current_part = line
            else:
                # Если одна строка слишком длинная, разбиваем её
                while len(line) > max_length:
                    parts.append(line[:max_length])
                    line = line[max_length:]
                current_part = line
        else:
            if current_part:
                current_part += '\n' + line
            else:
                current_part = line
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part.strip())
    
    return parts
