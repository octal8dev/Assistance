"""
Улучшенный GPT сервис для телеграм бота
Основан на оригинальном gpt_service.py с дополнительными возможностями
"""
import os
import sys
import asyncio
import logging
import random
import time
from typing import Optional, Dict, Any, List

# Простой импорт g4f
import g4f

logger = logging.getLogger(__name__)

class BotGPTService:
    """Сервис для работы с GPT через библиотеку g4f для телеграм бота"""
    
    def __init__(self):
        # ПРОВЕРЕННЫЕ РАБОЧИЕ ПРОВАЙДЕРЫ (из оригинального файла)
        
        # Быстрые провайдеры (до 3 секунд)
        self.fast_providers = [
            'Chatai',             # 0.78с - самый быстрый
            'AnyProvider',        # 0.98с - очень быстрый
            'Blackbox',           # 2.14с - стабильный для кода
            'OpenAIFM',           # 2.34с - быстрый
            'Qwen_Qwen_2_5_Max',  # 2.46с - быстрый
            'OIVSCodeSer0501',    # 2.53с - стабильный
            'WeWordle',           # 2.54с - быстрый
            'CohereForAI_C4AI_Command', # 2.58с - стабильный
        ]
        
        # Средние провайдеры (3-6 секунд) - БЕЗ Free2GPT!
        self.medium_providers = [
            'OIVSCodeSer2',       # 4.76с - стабильный
            'Qwen_Qwen_2_5',      # 5.25с - хороший (НЕ поддерживает vision!)
            'Yqcloud',            # 5.64с - работает
        ]
        
        # Медленные провайдеры (больше 6 секунд, но работают)
        self.slow_providers = [
            'ImageLabs',          # 8.27с - для изображений
            'Qwen_Qwen_3',        # 15.45с - умный но медленный
            'LambdaChat',         # 16.67с - с рассуждениями
            'BlackForestLabs_Flux1Dev', # 23.02с - для изображений
        ]
        
        # Провайдеры с поддержкой изображений (vision)
        self.vision_providers = [
            'PollinationsAI',     # ✅ 8.95с - РАБОТАЕТ с gpt-4o, РЕАЛЬНО ВИДИТ ИЗОБРАЖЕНИЯ!
        ]
        
        # Провайдеры для генерации изображений
        self.image_providers = [
            'ImageLabs',          # ✅ Генерирует изображения (SD XL)
            'BlackForestLabs_Flux1Dev',  # ✅ Генерирует изображения (Flux.1 Dev)
        ]
        
        # Проблематичные провайдеры (исключаем)
        self.problematic_providers = [
            'Free2GPT',           # Отправляет ответы на китайском языке
        ]
        
        # Основные рабочие провайдеры
        self.working_providers = self.fast_providers + self.medium_providers
        
        # Резервные провайдеры
        self.backup_providers = self.slow_providers
        
        self.current_provider = 'Chatai'  # Самый быстрый
        self.default_model = g4f.models.default
        
        # Настройки прокси - отключаем по умолчанию
        self.proxy = None
        self.use_proxy = False
        
        # Статистика провайдеров
        self.provider_stats = {}
        self.max_retries = 3
        
        # Карта моделей для vision провайдеров
        self.vision_model_map = {
            'PollinationsAI': 'gpt-4o',
        }
    
    def get_all_providers(self) -> List[str]:
        """Получить список всех провайдеров"""
        seen = set()
        ordered = []
        for p in self.fast_providers + self.medium_providers + self.slow_providers:
            if p not in seen:
                ordered.append(p)
                seen.add(p)
        return ordered
    
    def trim_history(self, history: list, max_length: int = 50000) -> list:
        """Обрезка истории разговора"""
        if not history:
            return history
            
        # Ограничиваем количество сообщений
        if len(history) > 50:  # Максимум 50 сообщений
            history = history[-50:]
        
        # Проверяем общую длину
        current_length = sum(len(str(message.get("content", ""))) for message in history)
        
        # Удаляем старые сообщения если слишком длинно
        while history and current_length > max_length:
            removed_message = history.pop(0)
            current_length -= len(str(removed_message.get("content", "")))
        
        return history
    
    async def get_response_async(self, message: str, conversation_history: list = None, 
                                model: str = None, providers: list = None, 
                                image_data: str = None, chat_id: int = None) -> Dict[str, Any]:
        """Асинхронное получение ответа от GPT"""
        
        # Подготавливаем историю разговора
        chat_history = []
        
        # Системный промпт для телеграм бота
        system_prompt = """Ты умный AI ассистент в Telegram боте.

ПРИНЦИПЫ РАБОТЫ:
1. Отвечай кратко и по делу
2. Используй эмодзи для лучшего восприятия 
3. Структурируй ответы списками и заголовками
4. Если вопрос сложный - разбивай на этапы
5. Всегда будь полезным и дружелюбным

ФОРМАТИРОВАНИЕ:
- Используй *жирный текст* для важного
- Используй `код` для технических терминов
- Используй списки для структурирования
- Добавляй эмодзи в начало ответа

СТИЛЬ: Профессиональный, но дружелюбный помощник."""

        chat_history.append({"role": "system", "content": system_prompt})
        
        # Получаем историю из БД если есть chat_id
        if chat_id:
            try:
                from ..database import db_manager
                if db_manager:
                    db_history = await db_manager.get_chat_history(chat_id, limit=10)
                    logger.info(f"[DB_HISTORY] Загружено {len(db_history)} сообщений для чата {chat_id}")
                    
                    # Конвертируем историю из БД
                    for hist_msg in db_history:
                        if hist_msg.get("message_type") == "user":
                            chat_history.append({
                                "role": "user", 
                                "content": str(hist_msg.get("message", ""))
                            })
                        elif hist_msg.get("message_type") == "assistant":
                            response_text = hist_msg.get("response") or hist_msg.get("message", "")
                            chat_history.append({
                                "role": "assistant", 
                                "content": str(response_text)
                            })
            except Exception as e:
                logger.warning(f"[DB_HISTORY] Ошибка загрузки истории: {e}")
        
        # Добавляем переданную историю
        if conversation_history:
            for msg in conversation_history:
                if msg.get("message"):
                    chat_history.append({"role": "user", "content": str(msg.get("message"))})
                if msg.get("response"):
                    chat_history.append({"role": "assistant", "content": str(msg.get("response"))})
        
        # Добавляем текущее сообщение
        if image_data:
            # Сообщение с изображением
            image_url = image_data
            if not image_data.startswith('data:'):
                image_url = f"data:image/jpeg;base64,{image_data}"
            
            current_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": str(message) if message else "Опиши что ты видишь на изображении"
                    },
                    {
                        "type": "image_url", 
                        "image_url": {
                            "url": image_url,
                            "detail": "high"
                        }
                    }
                ]
            }
            chat_history.append(current_message)
            logger.info(f"[VISION] Добавлено сообщение с изображением")
        else:
            # Обычное текстовое сообщение
            chat_history.append({"role": "user", "content": str(message)})
        
        # Определяем провайдеры для использования
        if image_data:
            # Для изображений используем только vision провайдеры
            providers_to_try = self.vision_providers
            model_to_use = 'gpt-4o'
            logger.info(f"[VISION] Используем vision провайдеры: {providers_to_try}")
        elif providers:
            providers_to_try = providers
            model_to_use = model
        elif model and model != 'auto':
            providers_to_try = self.working_providers + self.backup_providers
            model_to_use = model
        else:
            # Авто режим - только быстрые и средние провайдеры
            providers_to_try = self.working_providers
            model_to_use = 'gpt-4'
        
        # Исключаем проблематичные провайдеры
        providers_to_try = [p for p in providers_to_try if p not in self.problematic_providers]
        
        # Создаем список для попыток (с циклическим обходом)
        current_index = 0
        if self.current_provider in providers_to_try:
            current_index = providers_to_try.index(self.current_provider)
        
        final_providers_list = []
        max_cycles = 2  # Максимум 2 полных круга
        total_providers = len(providers_to_try)
        
        for cycle in range(max_cycles):
            for i in range(total_providers):
                provider_index = (current_index + i) % total_providers
                provider = providers_to_try[provider_index]
                final_providers_list.append(provider)
        
        # Ограничиваем попытки
        final_providers_list = final_providers_list[:15]
        
        logger.info(f"[START] Обработка сообщения: '{message[:50]}...'")
        logger.info(f"[PROVIDERS] Будем пробовать {len(final_providers_list)} провайдеров")
        
        rate_limited_providers = set()
        
        for attempt, provider_name in enumerate(final_providers_list):
            try:
                # Сброс rate limit после полного круга
                if attempt > 0 and attempt % total_providers == 0:
                    rate_limited_providers.clear()
                
                # Пропускаем провайдеров с rate limit
                if provider_name in rate_limited_providers:
                    continue
                    
                logger.info(f"[ATTEMPT] Попытка {attempt + 1}: {provider_name}")
                
                # Дополнительная проверка для vision
                if image_data and provider_name not in self.vision_providers:
                    logger.warning(f"[VISION_SKIP] Пропускаем {provider_name} - не поддерживает vision")
                    continue
                
                # Получаем провайдера
                provider = self._get_provider_by_name(provider_name)
                if not provider:
                    logger.warning(f"[ERROR] Провайдер {provider_name} не найден")
                    continue
                
                # Выбираем модель
                final_model_to_use = model_to_use
                if image_data and provider_name in self.vision_model_map:
                    final_model_to_use = self.vision_model_map[provider_name]
                
                # Обработка модели
                if final_model_to_use:
                    try:
                        if hasattr(g4f.models, final_model_to_use.replace('-', '_')):
                            final_model_to_use = getattr(g4f.models, final_model_to_use.replace('-', '_'))
                        elif hasattr(g4f.models, final_model_to_use):
                            final_model_to_use = getattr(g4f.models, final_model_to_use)
                    except Exception:
                        final_model_to_use = g4f.models.default
                else:
                    final_model_to_use = g4f.models.default
                
                # Параметры запроса
                request_kwargs = {
                    "model": final_model_to_use,
                    "messages": chat_history,
                    "provider": provider,
                    "timeout": 90,  # Таймаут 90 секунд
                }
                
                # Засекаем время
                start_time = time.time()
                
                # Делаем запрос
                response = await g4f.ChatCompletion.create_async(**request_kwargs)
                
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                # Проверяем ответ
                if response and len(str(response).strip()) > 0:
                    response_text = str(response).strip()
                    
                    # Форматируем ответ
                    formatted_response = self.format_telegram_response(response_text)
                    
                    logger.info(f"[SUCCESS] Провайдер: {provider_name}, время: {response_time}с")
                    
                    # Обновляем статистику
                    self.provider_stats[provider_name] = self.provider_stats.get(provider_name, 0) + 1
                    self.current_provider = provider_name
                    
                    return {
                        "success": True,
                        "response": formatted_response,
                        "raw_response": response_text,
                        "model_used": str(final_model_to_use),
                        "provider_used": provider_name,
                        "attempt_number": attempt + 1,
                        "response_time": response_time,
                        "message_length": len(message),
                        "history_length": len(chat_history)
                    }
                else:
                    logger.warning(f"[WARNING] {provider_name} вернул пустой ответ")
                    
            except asyncio.TimeoutError:
                logger.warning(f"[TIMEOUT] {provider_name}: превышен таймаут")
                continue
            except Exception as e:
                error_msg = str(e)
                if "rate" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                    logger.warning(f"[RATE_LIMIT] {provider_name}: превышен лимит - {error_msg}")
                    rate_limited_providers.add(provider_name)
                    continue
                elif "available in" in error_msg.lower():
                    logger.warning(f"[RATE_LIMIT] {provider_name}: временно недоступен - {error_msg}")
                    rate_limited_providers.add(provider_name)
                    continue
                else:
                    logger.warning(f"[ERROR] {provider_name}: {error_msg}")
                continue
        
        # Если все провайдеры не сработали
        error_type = "vision провайдеры" if image_data else "AI провайдеры"
        logger.error(f"[FAILED] Все {error_type} недоступны!")
        
        error_response = f"🚫 Извините, все {error_type} временно недоступны. Попробуйте позже."
        
        return {
            "success": False,
            "error": f"Все {error_type} недоступны",
            "response": error_response,
            "total_attempts": len(final_providers_list),
            "rate_limited_count": len(rate_limited_providers),
            "image_request": bool(image_data)
        }
    
    def _get_provider_by_name(self, provider_name: str):
        """Получить провайдера по имени"""
        try:
            if hasattr(g4f.Provider, provider_name):
                return getattr(g4f.Provider, provider_name)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения провайдера {provider_name}: {e}")
            return None
    
    def get_response_sync(self, message: str, conversation_history: list = None, 
                         model: str = None, providers: list = None, 
                         image_data: str = None, chat_id: int = None) -> Dict[str, Any]:
        """Синхронное получение ответа от GPT"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.get_response_async(message, conversation_history, model, providers, image_data, chat_id)
                )
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "🚫 Критическая ошибка при обработке запроса. Попробуйте позже."
            }
    
    def format_telegram_response(self, response_text: str) -> str:
        """Форматирование ответа специально для Telegram"""
        if not response_text:
            return response_text
            
        import re
        
        formatted_text = response_text
        
        # 1. Убираем избыточные markdown символы которые не поддерживает Telegram
        formatted_text = re.sub(r'```(\w+)\n(.*?)\n```', r'```\n\2\n```', formatted_text, flags=re.DOTALL)
        
        # 2. Конвертируем заголовки в жирный текст
        formatted_text = re.sub(r'^#{1,6}\s+(.+)', r'*\1*', formatted_text, flags=re.MULTILINE)
        
        # 3. Сохраняем списки, но убираем лишние символы
        lines = formatted_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Обрабатываем списки
            if re.match(r'^\d+\.\s+', stripped):
                # Нумерованные списки оставляем как есть
                formatted_lines.append(line)
            elif re.match(r'^[-\*\+]\s+', stripped):
                # Маркированные списки конвертируем в единый формат
                content = re.sub(r'^[-\*\+]\s+', '', stripped)
                formatted_lines.append(f"• {content}")
            else:
                formatted_lines.append(line)
        
        formatted_text = '\n'.join(formatted_lines)
        
        # 4. Ограничиваем длину для Telegram (максимум 4096 символов)
        if len(formatted_text) > 4000:
            formatted_text = formatted_text[:3950] + "\n\n... _(сообщение обрезано)_"
        
        # 5. Убираем лишние пустые строки
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
        
        return formatted_text.strip()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Получить информацию о провайдерах"""
        return {
            "current": self.current_provider,
            "working_providers": len(self.working_providers),
            "backup_providers": len(self.backup_providers),
            "vision_providers": len(self.vision_providers),
            "provider_stats": self.provider_stats,
            "all": self.get_all_providers()
        }

# Глобальный экземпляр сервиса
bot_gpt_service = BotGPTService()
