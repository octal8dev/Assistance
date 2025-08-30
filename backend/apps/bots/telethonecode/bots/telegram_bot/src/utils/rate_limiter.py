"""
Утилиты для работы с rate limiting
"""
import time
from typing import Dict, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta

class RateLimiter:
    """
    Класс для ограничения частоты запросов
    """
    
    def __init__(self):
        # Словарь для хранения истории запросов по пользователям
        # user_id -> deque of timestamps
        self.user_requests: Dict[int, deque] = defaultdict(deque)
        
        # Словарь для хранения времени последнего запроса
        self.last_request: Dict[int, float] = {}
        
        # Настройки по умолчанию
        self.default_max_requests = 10  # Максимум запросов
        self.default_time_window = 60   # Временное окно в секундах
        self.default_cooldown = 1       # Минимальный интервал между запросами
    
    def is_allowed(self, user_id: int, max_requests: int = None, 
                   time_window: int = None, cooldown: int = None) -> Tuple[bool, str]:
        """
        Проверить, разрешен ли запрос от пользователя
        
        Args:
            user_id: ID пользователя
            max_requests: Максимум запросов в окне (по умолчанию из настроек)
            time_window: Временное окно в секундах (по умолчанию из настроек)
            cooldown: Минимальный интервал между запросами (по умолчанию из настроек)
            
        Returns:
            Tuple[bool, str]: (разрешен_ли_запрос, сообщение_об_ошибке)
        """
        current_time = time.time()
        
        # Используем настройки по умолчанию если не указаны
        max_requests = max_requests or self.default_max_requests
        time_window = time_window or self.default_time_window
        cooldown = cooldown or self.default_cooldown
        
        # Проверяем cooldown (минимальный интервал)
        if user_id in self.last_request:
            time_since_last = current_time - self.last_request[user_id]
            if time_since_last < cooldown:
                remaining = cooldown - time_since_last
                return False, f"Подождите {remaining:.1f} секунд перед следующим запросом"
        
        # Получаем историю запросов пользователя
        user_queue = self.user_requests[user_id]
        
        # Удаляем старые запросы (вне временного окна)
        cutoff_time = current_time - time_window
        while user_queue and user_queue[0] < cutoff_time:
            user_queue.popleft()
        
        # Проверяем лимит запросов
        if len(user_queue) >= max_requests:
            # Вычисляем время до следующего разрешенного запроса
            oldest_request = user_queue[0]
            wait_time = time_window - (current_time - oldest_request)
            return False, f"Превышен лимит запросов. Попробуйте через {wait_time:.1f} секунд"
        
        # Разрешаем запрос и обновляем статистику
        user_queue.append(current_time)
        self.last_request[user_id] = current_time
        
        return True, ""
    
    def get_user_stats(self, user_id: int, time_window: int = None) -> Dict[str, any]:
        """
        Получить статистику запросов пользователя
        
        Args:
            user_id: ID пользователя
            time_window: Временное окно для подсчета (по умолчанию из настроек)
            
        Returns:
            Словарь со статистикой
        """
        current_time = time.time()
        time_window = time_window or self.default_time_window
        
        user_queue = self.user_requests[user_id]
        
        # Удаляем старые запросы
        cutoff_time = current_time - time_window
        while user_queue and user_queue[0] < cutoff_time:
            user_queue.popleft()
        
        # Время последнего запроса
        last_request_time = self.last_request.get(user_id, 0)
        time_since_last = current_time - last_request_time if last_request_time else None
        
        return {
            "requests_in_window": len(user_queue),
            "max_requests": self.default_max_requests,
            "time_window": time_window,
            "last_request_ago": time_since_last,
            "can_request_now": len(user_queue) < self.default_max_requests and 
                              (time_since_last is None or time_since_last >= self.default_cooldown)
        }
    
    def reset_user(self, user_id: int):
        """
        Сбросить ограничения для пользователя (для админов)
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.user_requests:
            self.user_requests[user_id].clear()
        if user_id in self.last_request:
            del self.last_request[user_id]
    
    def cleanup(self, max_age_hours: int = 24):
        """
        Очистка старых записей для экономии памяти
        
        Args:
            max_age_hours: Максимальный возраст записей в часах
        """
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        # Очищаем историю запросов
        users_to_remove = []
        for user_id, user_queue in self.user_requests.items():
            # Удаляем старые запросы
            while user_queue and user_queue[0] < cutoff_time:
                user_queue.popleft()
            
            # Если очередь пуста, помечаем пользователя для удаления
            if not user_queue:
                users_to_remove.append(user_id)
        
        # Удаляем пустые записи
        for user_id in users_to_remove:
            del self.user_requests[user_id]
        
        # Очищаем старые записи последних запросов
        last_requests_to_remove = [
            user_id for user_id, last_time in self.last_request.items()
            if last_time < cutoff_time
        ]
        
        for user_id in last_requests_to_remove:
            del self.last_request[user_id]

# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()
