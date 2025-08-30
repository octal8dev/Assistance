# Простой импорт g4f (версия 0.4.9.9 - без проблемного Airforce)
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

class GPTService:
    """Сервис для работы с GPT через библиотеку g4f"""
    
    def __init__(self):
        # ПРОВЕРЕННЫЕ РАБОЧИЕ ПРОВАЙДЕРЫ (протестировано 2025-07-05, 16 из 90)
        
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
            # 'Free2GPT',         # ИСКЛЮЧЕН - отправляет ответы на китайском языке!
        ]
        
        # Медленные провайдеры (больше 6 секунд, но работают)
        self.slow_providers = [
            'ImageLabs',          # 8.27с - для изображений
            'Qwen_Qwen_3',        # 15.45с - умный но медленный
            'LambdaChat',         # 16.67с - с рассуждениями
            'BlackForestLabs_Flux1Dev', # 23.02с - для изображений
        ]
        
        # Провайдеры с поддержкой изображений (vision) - ПРОТЕСТИРОВАНО С РЕАЛЬНЫМ ИЗОБРАЖЕНИЕМ!
        self.vision_providers = [
            # ЕДИНСТВЕННЫЙ ПРОВЕРЕННЫЙ VISION ПРОВАЙДЕР (протестировано с лина.jpg 22.07.2025)
            'PollinationsAI',             # ✅ 8.95с - РАБОТАЕТ с gpt-4o, РЕАЛЬНО ВИДИТ ИЗОБРАЖЕНИЯ!
        ]
        
        # Провайдеры для генерации изображений (image generation)
        self.image_providers = [
            'ImageLabs',          # ✅ Генерирует изображения (SD XL)
            'BlackForestLabs_Flux1Dev',  # ✅ Генерирует изображения (Flux.1 Dev)
        ]
        
        # Провайдеры БЕЗ поддержки изображений (исключаем из vision)
        self.no_vision_providers = [
            'Chatai',              # Быстрый, но без vision (заблокирован)
            'WeWordle',            # Без vision
            'OIVSCodeSer0501',     # Без vision (протестировано - требует API ключи)
            'OIVSCodeSer2',        # Без vision (протестировано - не видит изображения)
            'Yqcloud',             # Без vision
            'LambdaChat',          # Без vision
            'ImageLabs',           # Только для генерации изображений, не vision
        ]
        
        # ИСКЛЮЧЕННЫЕ провайдеры (НЕ РАБОТАЮТ с vision) - ОБНОВЛЕНО ПОСЛЕ ТЕСТИРОВАНИЯ
        self.blocked_vision_providers = [
            # Требуют API ключи (протестировано 22.07.2025)
            'DeepInfraChat',      # Требует аутентификацию (403 ошибка)
            'OIVSCodeSer0501',    # Требует API ключи (401 ошибка)
            'Anthropic',          # Требует API ключ
            'DeepInfra',          # Требует API ключ  
            'Groq',               # Требует API ключ
            'GeminiPro',          # Требует API ключ
            'CablyAI',            # Требует API ключ
            
            # Не найдены в g4f.Provider (протестировано 22.07.2025)
            'DocsBot',            # Не найден в g4f.Provider
            'OIVSCodeSer5',       # Не найден в g4f.Provider
            
            # Заблокированы
            'You',                # Заблокирован Cloudflare
            'Chatai',             # Заблокирован
            'Cloudflare',         # Заблокирован
            
            # Говорят что не видят изображения
            'Qwen_Qwen_2_72B',    # Говорит "не могу видеть изображения"
        ]
        
        # Основные рабочие провайдеры (быстрые + средние)
        self.working_providers = self.fast_providers + self.medium_providers
        
        # Резервные провайдеры (медленные, но работают)
        self.backup_providers = self.slow_providers
        
        # Нерабочие провайдеры (для справки)
        self.blocked_providers = [
            'You',                # Заблокирован Cloudflare
            'HuggingChat',        # Требует nodriver
            'DeepInfra',          # Требует API key
            'OpenaiChat',         # Требует HAR файл
            'Groq',               # Требует API key
            'MetaAI',             # Не работает
            'Copilot',            # Требует curl_cffi
            'DeepSeek',           # Требует API key
            'HuggingFace',        # Требует API key
        ]
        
        # Проблематичные провайдеры (работают, но с проблемами)
        self.problematic_providers = [
            'Free2GPT',           # Отправляет ответы на китайском языке!!!
        ]
        
        self.current_provider = 'Chatai'  # Самый быстрый
        self.default_model = g4f.models.default
        
        # Настройки прокси - отключаем по умолчанию
        self.proxy = "http://95.164.200.12:9459"
        self.use_proxy = False  # Прямое соединение работает лучше
        
        # Статистика провайдеров
        self.provider_stats = {}
        self.max_retries = 3
        
    def get_all_providers(self) -> List[str]:
        """Получить список всех провайдеров (по кругу, в правильном порядке)"""
        # Возвращает список: быстрые + средние + медленные (без дубликатов, в порядке обхода)
        seen = set()
        ordered = []
        for p in self.fast_providers + self.medium_providers + self.slow_providers:
            if p not in seen:
                ordered.append(p)
                seen.add(p)
        return ordered
        
    def trim_history(self, history: list, max_length: int = 50000) -> list:
        """Обрезка истории разговора - МИНИМАЛЬНАЯ обрезка только при критической длине"""
        if not history:
            return history
            
        # Увеличиваем лимиты во много раз!
        if len(history) > 100:  # Максимум 100 сообщений в истории (было 6)
            history = history[-100:]
        
        # Проверяем общую длину - критический лимит
        current_length = sum(len(str(message.get("content", ""))) for message in history)
        
        # Только если КРИТИЧЕСКИ длинно, удаляем старые сообщения
        while history and current_length > max_length:
            removed_message = history.pop(0)
            current_length -= len(str(removed_message.get("content", "")))
        
        return history
    
    async def get_response_async(self, message: str, conversation_history: list = None, model: str = None, providers: list = None, image_data: str = None, chat_id: int = None) -> Dict[str, Any]:
        """Асинхронное получение ответа от GPT с множественными попытками и использованием истории из БД"""
        
        # Карта моделей для vision провайдеров
        self.vision_model_map = {
            # ЕДИНСТВЕННЫЙ ПРОВЕРЕННЫЙ VISION ПРОВАЙДЕР (протестировано с реальным изображением)
            'PollinationsAI': 'gpt-4o',              # ✅ ПРОТЕСТИРОВАНО - РАБОТАЕТ отлично!
        }
        
        # Подготавливаем историю разговора
        chat_history = []
        
        # Добавляем системный промпт дизайнера с реальными примерами
        designer_system_prompt = """Ты опытный дизайнер студии "Vaaks Design" с многолетним опытом работы с клиентами.

ТВОЙ СТИЛЬ ОБЩЕНИЯ (скопируй точно):

ПРИМЕР 1 - Простое приветствие:
Клиент: "Привет"
Ты: "Привет!"

ПРИМЕР 2 - Приветствие с вопросом о проекте:
Клиент: "Привет! Как дела с проектом?"
Ты: "Привет! Сейчас уточню у команды, вернусь с ответом"

ПРИМЕР 3 - Работа с референсами (БЕЗ повторного приветствия):
Клиент: "Я хочу что-то из этих референсов"
Ты: "Спасибо! Передал ваши референсы команде. Вернусь с ответом в течение дня.

Есть дополнительные пожелания?"

ПРИМЕР 4 - Технические вопросы:
Клиент: "Есть ли эта картинка в векторном формате?"
Ты: "Уточним у команды, вернусь с ответом"

КЛЮЧЕВЫЕ ПРИНЦИПЫ:
1. ПРОВЕРЯЙ ИСТОРИЮ! Если уже здоровались в этом разговоре - НЕ здоровайся снова!
2. На ПЕРВОЕ "привет" отвечай "Привет!" - НЕ добавляй "Как дела?"
3. На ПОВТОРНОЕ "привет" в том же разговоре отвечай сразу по делу без приветствия
4. Про "уточню у команды" говори ТОЛЬКО если клиент задал конкретный вопрос о работе
5. Будь естественным и живым, не роботом
6. Короткие ответы лучше длинных

ВАЖНО: На технические вопросы отвечай: "Уточним у команды, вернусь с ответом"

ТВОЯ РОЛЬ: Живой менеджер дизайн-студии, который общается естественно."""

        chat_history.append({"role": "system", "content": designer_system_prompt})
        
        # ПОЛУЧАЕМ ИСТОРИЮ ИЗ БАЗЫ ДАННЫХ (если передан chat_id)
        if chat_id:
            try:
                # Импортируем database_manager здесь, чтобы избежать циклического импорта
                from database import db_manager
                
                # Получаем последние 20 сообщений из истории чата
                db_history = await db_manager.get_chat_history(chat_id, limit=20)
                logger.info(f"[DB_HISTORY] Загружено {len(db_history)} сообщений из истории чата {chat_id}")
                
                # Конвертируем историю из БД в формат для GPT
                for hist_msg in db_history:
                    if hist_msg.get("message_type") == "user":
                        chat_history.append({
                            "role": "user", 
                            "content": str(hist_msg.get("message", ""))
                        })
                    elif hist_msg.get("message_type") == "assistant" or hist_msg.get("response"):
                        # Это ответ бота
                        response_text = hist_msg.get("response") or hist_msg.get("message", "")
                        chat_history.append({
                            "role": "assistant", 
                            "content": str(response_text)
                        })
                
            except Exception as e:
                logger.warning(f"[DB_HISTORY] Ошибка загрузки истории из БД для чата {chat_id}: {e}")
                # Продолжаем работу без истории из БД
        
        # Добавляем переданную историю разговора (если есть) - ДОПОЛНИТЕЛЬНО к истории из БД
        if conversation_history:
            logger.info(f"[PARAM_HISTORY] Добавляем {len(conversation_history)} сообщений из параметра")
            # Берем ВСЕ сообщения из переданной истории
            for msg in conversation_history:  
                if msg.get("message"):
                    user_content = str(msg.get("message", ""))
                    chat_history.append({"role": "user", "content": user_content})
                
                if msg.get("response"):
                    ai_content = str(msg.get("response", ""))
                    chat_history.append({"role": "assistant", "content": ai_content})
        
        # Добавляем текущее сообщение с поддержкой изображений
        if image_data:
            # Обрабатываем разные форматы изображений
            image_url = image_data
            if not image_data.startswith('data:'):
                # Если это не data URL, добавляем префикс для base64
                if image_data.startswith('/'):
                    # Локальный путь к файлу
                    image_url = f"data:image/jpeg;base64,{image_data}"
                else:
                    # Предполагаем, что это уже base64 данные
                    image_url = f"data:image/jpeg;base64,{image_data}"
            
            # Если есть изображение, создаем сообщение с мультимедиа контентом
            current_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": str(message) if message else "Опиши что ты видишь на изображении подробно"
                    },
                    {
                        "type": "image_url", 
                        "image_url": {
                            "url": image_url,
                            "detail": "high"  # Высокое качество анализа изображения
                        }
                    }
                ]
            }
            chat_history.append(current_message)
            logger.info(f"[VISION] Добавлено сообщение с изображением. Текст: '{message[:100] if message else 'Нет текста'}'")
            logger.info(f"[VISION] Формат изображения: {'data URL' if image_data.startswith('data:') else 'base64'}")
        else:
            # Обычное текстовое сообщение
            chat_history.append({"role": "user", "content": str(message)})
        
        # Определяем список провайдеров для использования
        if image_data:
            # ДЛЯ ИЗОБРАЖЕНИЙ ВСЕГДА ИСПОЛЬЗУЕМ ТОЛЬКО VISION ПРОВАЙДЕРЫ! (приоритет выше всего)
            providers_to_try = self.vision_providers
            model_to_use = 'gpt-4o'  # Лучшая модель для vision от OpenAI
            logger.info(f"[VISION] Обнаружено изображение! Принудительно используем ТОЛЬКО vision провайдеры: {providers_to_try}")
            logger.info(f"[VISION] Модель для vision: {model_to_use}")
        elif providers:
            # Конкретная модель с несколькими провайдерами (только для текста)
            providers_to_try = providers
            model_to_use = model
        elif model and model != 'auto':
            # Конкретная модель, используем все совместимые провайдеры
            providers_to_try = self.fast_providers + self.medium_providers + self.backup_providers
            model_to_use = model
        else:
            # Авто режим - используем только рабочие провайдеры с базовой моделью gpt-4
            providers_to_try = self.working_providers  # Только быстрые и средние провайдеры
            model_to_use = 'gpt-4'  # Базовая модель для авто режима
        
        # Исключаем проблематичные провайдеры из всех случаев
        providers_to_try = [p for p in providers_to_try if p not in self.problematic_providers]
        logger.info(f"[SAFETY] Исключены проблематичные провайдеры: {self.problematic_providers}")
        logger.info(f"[FINAL] Итоговый список провайдеров: {providers_to_try}")
        
        # Начинаем с текущего провайдера, затем идем по кругу
        current_index = 0
        if self.current_provider in providers_to_try:
            current_index = providers_to_try.index(self.current_provider)
        
        # Создаем циклический список провайдеров (можем пройти несколько кругов)
        final_providers_list = []
        max_cycles = 3  # Максимум 3 полных круга по всем провайдерам
        total_providers = len(providers_to_try)
        
        for cycle in range(max_cycles):
            for i in range(total_providers):
                provider_index = (current_index + i) % total_providers
                provider = providers_to_try[provider_index]
                
                # Если это первый цикл, добавляем всех провайдеров
                # Если не первый цикл, добавляем только если провайдер еще не пробовался в этой сессии
                if cycle == 0 or provider not in [p for p in final_providers_list[:total_providers]]:
                    final_providers_list.append(provider)
        
        # Ограничиваем общее количество попыток
        final_providers_list = final_providers_list[:30]  # Максимум 30 попыток
        
        logger.info(f"[START] Начинаем обработку сообщения: '{message[:50]}...'")
        logger.info(f"[HISTORY] История содержит {len(chat_history)} сообщений")
        logger.info(f"[MODEL] Используем модель: {model_to_use}")
        logger.info(f"[IMAGE] Изображение: {'Да' if image_data else 'Нет'}")
        logger.info(f"[PROVIDERS] Будем пробовать {len(final_providers_list)} провайдеров циклически")
        
        rate_limited_providers = set()  # Отслеживаем провайдеров с rate limit
        
        for attempt, provider_name in enumerate(final_providers_list):
            try:
                # Если прошли полный круг по всем провайдерам, сбрасываем rate limit список
                if attempt > 0 and attempt % total_providers == 0:
                    logger.info(f"[RESET] Прошли полный круг, сбрасываем rate limit список")
                    rate_limited_providers.clear()
                
                # Пропускаем провайдеров, которые недавно показали rate limit
                if provider_name in rate_limited_providers:
                    logger.info(f"[SKIP] Пропускаем {provider_name} - недавно был rate limit")
                    continue
                    
                logger.info(f"[ATTEMPT] Попытка {attempt + 1}/{len(final_providers_list)}: {provider_name}")
                
                # ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: если есть изображение, разрешаем только vision провайдеры
                if image_data and provider_name not in self.vision_providers:
                    logger.warning(f"[VISION_SKIP] Пропускаем {provider_name} - не поддерживает vision при наличии изображения")
                    continue
                
                # Получаем провайдера
                provider = self._get_provider_by_name(provider_name)
                if not provider:
                    logger.warning(f"[ERROR] Провайдер {provider_name} не найден в g4f")
                    continue
                
                # Подготавливаем параметры запроса
                # Для vision провайдеров используем специальные модели
                final_model_to_use = model_to_use
                
                # Если это vision запрос, выбираем лучшую модель для конкретного провайдера
                if image_data and provider_name in self.vision_model_map:
                    vision_model = self.vision_model_map[provider_name]
                    logger.info(f"[VISION] Для провайдера {provider_name} используем модель: {vision_model}")
                    final_model_to_use = vision_model
                
                # Попробуем найти модель в g4f.models
                if final_model_to_use:
                    try:
                        if hasattr(g4f.models, final_model_to_use.replace('-', '_')):
                            final_model_to_use = getattr(g4f.models, final_model_to_use.replace('-', '_'))
                        elif hasattr(g4f.models, final_model_to_use):
                            final_model_to_use = getattr(g4f.models, final_model_to_use)
                        else:
                            # Если модель не найдена в g4f.models, используем строку
                            final_model_to_use = final_model_to_use
                    except Exception as e:
                        logger.warning(f"[MODEL] Ошибка при поиске модели {final_model_to_use}: {e}")
                        # В случае ошибки используем дефолтную модель
                        final_model_to_use = g4f.models.default
                else:
                    final_model_to_use = g4f.models.default
                
                request_kwargs = {
                    "model": final_model_to_use,
                    "messages": chat_history,
                    "provider": provider,
                    "timeout": 120,  # Увеличиваем таймаут до 2 минут!
                }
                
                # Добавляем прокси только если включен и попытка > 2
                if self.use_proxy and self.proxy and attempt > 2:
                    request_kwargs["proxy"] = self.proxy
                    logger.info(f"[PROXY] Используем прокси: {self.proxy}")
                else:
                    logger.info(f"[DIRECT] Прямое соединение (без прокси)")
                
                # Засекаем время
                start_time = time.time()
                
                # Делаем запрос как в примере
                response = await g4f.ChatCompletion.create_async(**request_kwargs)
                
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                # Проверяем ответ
                if response and len(str(response).strip()) > 0:
                    response_text = str(response).strip()
                    
                    # Применяем форматирование как в ChatGPT
                    formatted_response = self.format_response(response_text)
                    
                    logger.info(f"[SUCCESS] Успех! Провайдер: {provider_name}, время: {response_time}с")
                    
                    # Обновляем статистику
                    self.provider_stats[provider_name] = self.provider_stats.get(provider_name, 0) + 1
                    self.current_provider = provider_name
                    
                    return {
                        "success": True,
                        "response": formatted_response,  # Возвращаем отформатированный ответ
                        "raw_response": response_text,   # Сохраняем оригинал для отладки
                        "model_used": "gpt-3.5-turbo",
                        "provider_used": provider_name,
                        "attempt_number": attempt + 1,
                        "response_time": response_time,
                        "proxy_used": self.use_proxy,
                        "message_length": len(message),
                        "history_length": len(chat_history)
                    }
                else:
                    logger.warning(f"[WARNING] {provider_name} вернул пустой ответ")
                    
            except asyncio.TimeoutError:
                logger.warning(f"[TIMEOUT] {provider_name}: превышен таймаут")
                continue
            except ConnectionError as e:
                logger.warning(f"[CONNECTION] {provider_name}: ошибка соединения - {str(e)}")
                continue
            except Exception as e:
                error_msg = str(e)
                if "proxy" in error_msg.lower():
                    logger.warning(f"[PROXY] {provider_name}: проблема с прокси - {error_msg}")
                elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                    logger.warning(f"[CONNECTION] {provider_name}: проблема соединения - {error_msg}")
                elif "rate" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                    logger.warning(f"[RATE_LIMIT] {provider_name}: превышен лимит запросов - {error_msg}")
                    # Добавляем провайдера в список с rate limit
                    rate_limited_providers.add(provider_name)
                    # НЕ делаем паузу - сразу переходим к следующему провайдеру
                    continue
                elif "block" in error_msg.lower() or "forbidden" in error_msg.lower():
                    logger.warning(f"[BLOCKED] {provider_name}: заблокирован - {error_msg}")
                elif "available in" in error_msg.lower():
                    logger.warning(f"[RATE_LIMIT] {provider_name}: провайдер временно недоступен - {error_msg}")
                    # Добавляем провайдера в список с rate limit
                    rate_limited_providers.add(provider_name)
                    # НЕ делаем паузу - сразу переходим к следующему провайдеру
                    continue
                elif image_data and ("vision" in error_msg.lower() or "image" in error_msg.lower() or "multimodal" in error_msg.lower()):
                    logger.warning(f"[VISION_ERROR] {provider_name}: ошибка обработки изображения - {error_msg}")
                    # Для vision ошибок сразу переходим к следующему провайдеру
                    continue
                elif image_data and "unsupported" in error_msg.lower():
                    logger.warning(f"[VISION_UNSUPPORTED] {provider_name}: не поддерживает изображения - {error_msg}")
                    continue
                else:
                    logger.warning(f"[ERROR] {provider_name}: {error_msg}")
                continue
            
            # Минимальная пауза только для сетевых ошибок
            if "connection" in str(e).lower() or "network" in str(e).lower():
                await asyncio.sleep(0.1)  # Очень короткая пауза только для сетевых проблем
        
        # Если все провайдеры не сработали
        error_type = "vision провайдеры" if image_data else "провайдеры"
        logger.error(f"[FAILED] Все {error_type} недоступны! Попробовано: {len(final_providers_list)}, rate limited: {len(rate_limited_providers)}")
        
        error_response = f"Извините, сейчас все AI {error_type} недоступны. Попробуйте позже"
        if image_data:
            error_response += " или загрузите изображение позже"
        error_response += "."
        
        return {
            "success": False,
            "error": f"Все {error_type} недоступны",
            "response": error_response,
            "total_attempts": len(final_providers_list),
            "rate_limited_count": len(rate_limited_providers),
            "provider_stats": self.provider_stats,
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
    
    def get_response_sync(self, message: str, conversation_history: list = None, model: str = None, providers: list = None, image_data: str = None, chat_id: int = None) -> Dict[str, Any]:
        """Синхронное получение ответа от GPT с поддержкой истории из БД"""
        try:
            # Простое выполнение асинхронной функции
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.get_response_async(message, conversation_history, model, providers, image_data, chat_id))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Критическая ошибка: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Критическая ошибка при обработке запроса. Попробуйте позже."
            }
    
    def get_current_provider(self) -> str:
        """Получить текущего провайдера"""
        return self.current_provider
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Получить информацию о провайдерах"""
        return {
            "current": self.current_provider,
            "model": str(self.default_model),
            "proxy": self.proxy if self.use_proxy else None,
            "proxy_enabled": self.use_proxy,
            "working_providers": len(self.working_providers),
            "backup_providers": len(self.backup_providers),
            "vision_providers": len(self.vision_providers),
            "provider_stats": self.provider_stats,
            "all": self.get_all_providers(),
            "vision_list": self.vision_providers,
            "no_vision_list": self.no_vision_providers,
        }
    
    def toggle_proxy(self, enable: bool = None) -> bool:
        """Переключить прокси"""
        if enable is None:
            self.use_proxy = not self.use_proxy
        else:
            self.use_proxy = enable
        return self.use_proxy
    
    def format_response(self, response_text: str) -> str:
        """Форматирование ответа как в ChatGPT с markdown разметкой"""
        if not response_text:
            return response_text
            
        formatted_text = response_text
        
        # 1. Обрабатываем блоки кода (многострочные)
        import re
        
        # Сначала блоки кода с языком
        formatted_text = re.sub(r'```(\w+)\n(.*?)\n```', r'```\1\n\2\n```', formatted_text, flags=re.DOTALL)
        # Потом блоки кода без языка
        formatted_text = re.sub(r'```\n?(.*?)\n?```', r'```\n\1\n```', formatted_text, flags=re.DOTALL)
        
        # 2. Инлайн код (только если не внутри блока кода)
        def replace_inline_code(match):
            code = match.group(1)
            if '\n' not in code and len(code.strip()) < 100:
                return f'`{code}`'
            return match.group(0)
        
        # Применяем только вне блоков кода
        parts = formatted_text.split('```')
        for i in range(0, len(parts), 2):  # Только четные индексы (вне блоков кода)
            parts[i] = re.sub(r'`([^`\n]+)`', replace_inline_code, parts[i])
        formatted_text = '```'.join(parts)
        
        # 3. Обрабатываем строки по отдельности для заголовков и списков
        lines = formatted_text.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for line in lines:
            # Проверяем, находимся ли мы в блоке кода
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append(line)
                continue
                
            if in_code_block:
                formatted_lines.append(line)
                continue
            
            stripped = line.strip()
            
            # Заголовки (строки заканчивающиеся двоеточием, которые выглядят как заголовки)
            if (stripped.endswith(':') and 
                len(stripped) < 80 and 
                not stripped.startswith('#') and
                len(stripped.split()) <= 8):
                
                # Проверяем, что это действительно заголовок
                title_keywords = ['пример', 'example', 'результат', 'вывод', 'output', 'result',
                                'решение', 'ответ', 'объяснение', 'концепции', 'моменты',
                                'использование', 'применение', 'как', 'что', 'зачем']
                
                is_title = any(keyword in stripped.lower() for keyword in title_keywords)
                
                if is_title:
                    formatted_lines.append(f"## {stripped}")
                else:
                    formatted_lines.append(line)
            # Нумерованные списки
            elif re.match(r'^\d+\.\s+', stripped):
                formatted_lines.append(line)
            # Списки с дефисами
            elif re.match(r'^[-\*\+]\s+', stripped):
                formatted_lines.append(line)
            # Обычные строки, которые могут быть элементами списка
            elif (stripped and 
                  not stripped.startswith('#') and
                  len(stripped) < 200):
                # Если предыдущая или следующая строка - элемент списка, делаем эту строку тоже элементом
                prev_line = formatted_lines[-1].strip() if formatted_lines else ""
                next_idx = lines.index(line) + 1
                next_line = lines[next_idx].strip() if next_idx < len(lines) else ""
                
                is_list_context = (
                    re.match(r'^\d+\.\s+', prev_line) or
                    re.match(r'^[-\*\+]\s+', prev_line) or
                    re.match(r'^\d+\.\s+', next_line) or
                    re.match(r'^[-\*\+]\s+', next_line)
                )
                
                if is_list_context and len(stripped.split()) < 15:
                    formatted_lines.append(f"- {stripped}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        formatted_text = '\n'.join(formatted_lines)
        
        # 4. Обрабатываем выделение важного текста (только вне блоков кода)
        parts = formatted_text.split('```')
        for i in range(0, len(parts), 2):  # Только четные индексы (вне блоков кода)
            # Слова в КАПСЕ превращаем в **жирный текст**
            parts[i] = re.sub(r'\b([А-ЯЁ]{3,})\b', r'**\1**', parts[i])
            # Ключевые результаты
            parts[i] = re.sub(r'\b(Результат|Вывод|Output|Result):\s*', r'**\1:**\n', parts[i])
            parts[i] = re.sub(r'\b(Пример|Example):\s*', r'**\1:**\n', parts[i])
        
        formatted_text = '```'.join(parts)
        
        # 5. Убираем лишние пустые строки
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
        
        return formatted_text.strip()
    
    def change_provider(self, provider_name: str) -> bool:
        """Изменить текущего провайдера"""
        try:
            all_providers = self.get_all_providers()
            if provider_name in all_providers:
                self.current_provider = provider_name
                logger.info(f"Провайдер изменен на {provider_name}")
                return True
            else:
                logger.warning(f"Провайдер {provider_name} не найден в списке доступных")
                return False
        except Exception as e:
            logger.error(f"Ошибка при смене провайдера: {e}")
            return False

    async def generate_image(self, prompt: str, provider_name: str = None) -> Dict[str, Any]:
        """Генерация изображения из текстового описания
        
        Args:
            prompt: Текстовое описание изображения для генерации
            provider_name: Опциональный конкретный провайдер (ImageLabs или BlackForestLabs_Flux1Dev)
            
        Returns:
            Словарь с данными изображения или информацией об ошибке
        """
        # Если провайдер не указан, используем циклический перебор всех доступных
        try_all_providers = provider_name is None
        
        # Создаём список провайдеров для перебора
        providers_to_try = []
        
        if try_all_providers:
            # Пробуем все доступные провайдеры изображений
            providers_to_try = self.image_providers.copy()
            # Дублируем список для второго прохода на случай неудачи
            providers_to_try = providers_to_try + providers_to_try
        else:
            # Если указан конкретный провайдер, проверяем его допустимость
            if provider_name not in self.image_providers:
                return {
                    "success": False,
                    "error": f"Провайдер {provider_name} не является валидным провайдером изображений",
                    "available_providers": self.image_providers
                }
            providers_to_try = [provider_name]
        
        # Переменные для отслеживания ошибок
        quota_errors = []
        last_error = None
        
        logger.info(f"[IMAGE] Начинаем генерацию изображения: '{prompt[:50]}...'")
        
        # Перебираем провайдеры до первого успеха
        for current_provider in providers_to_try:
            try:
                logger.info(f"[IMAGE] Попытка генерации с провайдером: {current_provider}")
                
                # Получаем провайдер
                provider = self._get_provider_by_name(current_provider)
                if not provider:
                    logger.warning(f"[IMAGE] Провайдер {current_provider} не найден в g4f")
                    continue
                
                # Измеряем время выполнения
                start_time = time.time()
                
                # Ограничение по времени
                timeout_seconds = 60  # 60 секунд максимум
                
                # Создаем сообщения для запроса (некоторые провайдеры требуют этот формат)
                messages = [{"role": "user", "content": prompt}]
                
                # Отправляем запрос на генерацию изображения с таймаутом
                if current_provider == "ImageLabs":
                    # ImageLabs требует model и messages
                    image_data = await asyncio.wait_for(
                        g4f.ChatCompletion.create_async(
                            model=g4f.models.default,
                            messages=messages,
                            provider=provider,
                            # Дополнительные параметры для генерации изображений
                            **{"prompt": prompt, "image_model": "sd_xl_base_1.0"}
                        ),
                        timeout=timeout_seconds
                    )
                elif current_provider == "BlackForestLabs_Flux1Dev":
                    # BlackForestLabs Flux.1 Dev
                    image_data = await asyncio.wait_for(
                        g4f.ChatCompletion.create_async(
                            model=g4f.models.default,
                            messages=messages,
                            provider=provider,
                            **{"prompt": prompt}
                        ),
                        timeout=timeout_seconds
                    )
                else:
                    # Универсальный подход для других провайдеров
                    image_data = await asyncio.wait_for(
                        g4f.ChatCompletion.create_async(
                            model=g4f.models.default,
                            messages=messages,
                            provider=provider
                        ),
                        timeout=timeout_seconds
                    )
                
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                # Проверяем, что ответ не пустой
                if not image_data:
                    logger.warning(f"[IMAGE] Пустой ответ от провайдера {current_provider}")
                    continue
                
                # Проверяем на наличие сообщения о превышении квоты
                if isinstance(image_data, str) and any(keyword in image_data.lower() for keyword in 
                                                       ["quota", "квота", "exceeded", "limit", "wait", "ожидание"]):
                    # Извлекаем время ожидания из сообщения
                    import re
                    wait_time_match = re.search(r'(\d+)\s*(s|sec|seconds|секунд)', image_data.lower())
                    wait_time = wait_time_match.group(1) if wait_time_match else "неизвестно"
                    
                    error_msg = f"Квота провайдера {current_provider} исчерпана. Время ожидания: {wait_time} секунд"
                    logger.warning(f"[IMAGE] {error_msg}")
                    quota_errors.append(error_msg)
                    continue
                
                # Извлекаем URL изображения из ответа
                image_url = self._extract_image_url(image_data)
                
                logger.info(f"[IMAGE] SUCCESS! Провайдер: {current_provider}, время: {response_time}с")
                
                # Возвращаем успешный результат
                return {
                    "success": True,
                    "image_url": image_url,
                    "image_data": image_data,
                    "provider": current_provider,
                    "response_time": response_time,
                    "prompt": prompt
                }
                
            except asyncio.TimeoutError:
                logger.warning(f"[IMAGE] Таймаут при генерации изображения с {current_provider}")
                last_error = f"Превышено время ожидания ответа от {current_provider}"
                continue
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[IMAGE] Ошибка при генерации изображения с {current_provider}: {error_msg}")
                
                # Проверяем на ошибку квоты
                if any(keyword in error_msg.lower() for keyword in ["quota", "квота", "exceeded", "gpu quota", "limit"]):
                    import re
                    wait_time_match = re.search(r'(\d+)\s*(s|sec|seconds|секунд)', error_msg.lower())
                    wait_time = wait_time_match.group(1) if wait_time_match else "неизвестно"
                    
                    quota_error = f"Квота провайдера {current_provider} исчерпана. Время ожидания: {wait_time} секунд"
                    quota_errors.append(quota_error)
                    last_error = quota_error
                else:
                    last_error = f"Ошибка провайдера {current_provider}: {error_msg}"
                
                continue
        
        # Если все провайдеры не сработали
        if quota_errors:
            return {
                "success": False,
                "error": "Все провайдеры изображений исчерпали квоту",
                "quota_errors": quota_errors,
                "message": "Квота на генерацию изображений исчерпана. Пожалуйста, попробуйте позже."
            }
        else:
            return {
                "success": False,
                "error": last_error or "Не удалось сгенерировать изображение",
                "providers_tried": providers_to_try,
                "message": "Не удалось сгенерировать изображение. Пожалуйста, попробуйте другой запрос."
            }
    
    def _extract_image_url(self, text):
        """Универсальная функция для извлечения URL изображения из разных форматов текста"""
        if not text or not isinstance(text, str):
            return None
            
        import re
        
        # Метод 1: Извлечение URL из Markdown-формата [![alt](url)](url)
        pattern1 = r'!\[.*?\]\((https?://[^)]+)\)'
        match1 = re.search(pattern1, text)
        if match1:
            return match1.group(1)
        
        # Метод 2: Извлечение URL из обычного Markdown ![alt](url)
        pattern2 = r'!\[(.*?)\]\((https?://[^)]+)\)'
        match2 = re.search(pattern2, text)
        if match2:
            return match2.group(2)
        
        # Метод 3: Поиск любого URL в тексте
        pattern3 = r'(https?://[^\s)]+)'
        match3 = re.search(pattern3, text)
        if match3:
            return match3.group(1)
        
        # Метод 4: URL с относительным путем
        pattern4 = r'(//[^\s)]+)'
        match4 = re.search(pattern4, text)
        if match4:
            return f"https:{match4.group(1)}"
        
        # Метод 5: URL начинается с www.
        pattern5 = r'(www\.[^\s)]+)'
        match5 = re.search(pattern5, text)
        if match5:
            return f"https://{match5.group(1)}"
            
        return None

# Создаем глобальный экземпляр сервиса
gpt_service = GPTService()
