"""
Сервис для анализа сложности вопросов
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class QuestionComplexityAnalyzer:
    """Анализатор сложности вопросов"""
    
    def __init__(self):
        # Ключевые слова для определения сложности
        self.complex_keywords = [
            # Программирование
            'алгоритм', 'алгоритма', 'алгоритме', 'алгоритмы',
            'архитектура', 'архитектуры', 'архитектуре',
            'базы данных', 'база данных', 'бд', 'sql', 'nosql',
            'backend', 'frontend', 'fullstack',
            'микросервис', 'микросервисы', 'микросервисов',
            'паттерн', 'паттерны', 'паттернов', 'design pattern',
            'рефакторинг', 'рефакторинга',
            'оптимизация', 'оптимизации', 'оптимизировать',
            'производительность', 'производительности',
            'тестирование', 'тесты', 'тестов', 'unit test',
            'deploy', 'деплой', 'развертывание',
            'docker', 'kubernetes', 'контейнер', 'контейнеры',
            'api', 'rest api', 'graphql',
            'json', 'xml', 'yaml',
            'git', 'version control', 'контроль версий',
            
            # Технические термины
            'сервер', 'сервера', 'серверов',
            'клиент', 'клиента', 'клиентов',
            'протокол', 'протокола', 'протоколы',
            'безопасность', 'безопасности', 'security',
            'шифрование', 'шифрования', 'encryption',
            'authentication', 'авторизация', 'аутентификация',
            'токен', 'токены', 'токенов', 'jwt',
            'кеширование', 'кеш', 'cache',
            'load balancer', 'балансировщик',
            'cdn', 'content delivery network',
            
            # Математика и наука
            'интеграл', 'интегралы', 'интегралов',
            'производная', 'производные', 'производных',
            'дифференциал', 'дифференциалы',
            'матрица', 'матрицы', 'матриц',
            'вектор', 'векторы', 'векторов',
            'статистика', 'статистики', 'статистический',
            'вероятность', 'вероятности', 'вероятностный',
            'машинное обучение', 'machine learning', 'ml',
            'искусственный интеллект', 'artificial intelligence', 'ai',
            'нейронная сеть', 'нейронные сети', 'neural network',
            'deep learning', 'глубокое обучение',
            
            # Бизнес и экономика
            'бизнес-модель', 'бизнес модель', 'бизнес-план',
            'стратегия', 'стратегии', 'стратегический',
            'маркетинг', 'маркетинга', 'маркетинговый',
            'инвестиции', 'инвестиций', 'инвестировать',
            'финансы', 'финансов', 'финансовый',
            'экономика', 'экономики', 'экономический',
            'менеджмент', 'менеджмента', 'управление',
            'аналитика', 'аналитики', 'analytics',
            
            # Медицина и здоровье
            'диагностика', 'диагностики', 'диагноз',
            'лечение', 'лечения', 'терапия',
            'медицина', 'медицины', 'медицинский',
            'фармакология', 'препарат', 'препараты',
            'болезнь', 'заболевание', 'симптом', 'симптомы',
            
            # Юриспруденция
            'право', 'правовой', 'юридический',
            'закон', 'законы', 'законодательство',
            'договор', 'договоры', 'контракт',
            'суд', 'судебный', 'иск',
            'нормативный', 'регулирование',
        ]
        
        # Простые слова-индикаторы
        self.simple_indicators = [
            'что это', 'что такое', 'как дела', 'привет', 'hi', 'hello',
            'спасибо', 'пока', 'хорошо', 'плохо', 'да', 'нет',
            'погода', 'время', 'сколько времени',
        ]
        
        # Сложные конструкции
        self.complex_patterns = [
            r'как\s+реализовать',
            r'как\s+создать\s+[а-яё]+\s+систему',
            r'каким\s+образом',
            r'объясни\s+подробно',
            r'детальный\s+анализ',
            r'пошаговый\s+алгоритм',
            r'развернутый\s+ответ',
            r'техническое\s+решение',
            r'архитектурное\s+решение',
        ]
    
    def analyze_complexity(self, text: str) -> Dict[str, any]:
        """
        Анализирует сложность вопроса
        
        Args:
            text: Текст для анализа
            
        Returns:
            Словарь с результатами анализа
        """
        text_lower = text.lower()
        
        # Подсчет индикаторов сложности
        complexity_score = 0
        found_keywords = []
        found_patterns = []
        
        # Проверяем простые индикаторы
        simple_found = False
        for indicator in self.simple_indicators:
            if indicator in text_lower:
                simple_found = True
                break
        
        # Проверяем сложные ключевые слова
        for keyword in self.complex_keywords:
            if keyword in text_lower:
                complexity_score += 2
                found_keywords.append(keyword)
        
        # Проверяем сложные паттерны
        for pattern in self.complex_patterns:
            if re.search(pattern, text_lower):
                complexity_score += 3
                found_patterns.append(pattern)
        
        # Дополнительные факторы сложности
        word_count = len(text.split())
        if word_count > 20:
            complexity_score += 1
        
        if word_count > 50:
            complexity_score += 2
        
        # Проверяем наличие вопросительных конструкций
        question_patterns = [
            r'как\s+(?:можно\s+)?(?:лучше\s+)?(?:правильно\s+)?\w+',
            r'каким\s+способом',
            r'в\s+чем\s+(?:разница|отличие)',
            r'почему\s+(?:так\s+происходит|это\s+работает)',
            r'что\s+происходит\s+(?:когда|если)',
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, text_lower):
                complexity_score += 1
        
        # Определяем уровень сложности
        if simple_found and complexity_score < 2:
            complexity_level = "simple"
        elif complexity_score < 4:
            complexity_level = "medium"
        elif complexity_score < 8:
            complexity_level = "complex"
        else:
            complexity_level = "very_complex"
        
        result = {
            "complexity_level": complexity_level,
            "complexity_score": complexity_score,
            "found_keywords": found_keywords,
            "found_patterns": found_patterns,
            "word_count": word_count,
            "should_tag_human": complexity_level in ["complex", "very_complex"],
            "use_human_behavior": False  # По умолчанию для простых сообщений
        }
        
        logger.debug(f"Анализ сложности: '{text[:50]}...' -> {complexity_level} (score: {complexity_score})")
        
        return result
    
    def should_use_human_behavior(self, text: str, is_ask_command: bool = False) -> bool:
        """
        Определяет, нужно ли использовать эмуляцию человеческого поведения
        
        Args:
            text: Текст сообщения
            is_ask_command: Является ли это командой /ask
            
        Returns:
            True если нужно эмулировать человеческое поведение
        """
        # Команда /ask всегда использует человеческое поведение
        if is_ask_command:
            return True
        
        # Для обычных сообщений - только простые ответы
        return False
    
    def should_tag_human(self, text: str) -> bool:
        """
        Определяет, нужно ли тегать человека для сложного вопроса
        
        Args:
            text: Текст сообщения
            
        Returns:
            True если нужно тегать человека
        """
        analysis = self.analyze_complexity(text)
        return analysis["should_tag_human"]

# Глобальный экземпляр анализатора
complexity_analyzer = QuestionComplexityAnalyzer()
