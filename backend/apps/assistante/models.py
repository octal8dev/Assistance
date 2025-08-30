from django.db import models
from django.conf import settings

class BotSettings(models.Model):
    """Настройки Telegram-клиента для пользователя."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bot_settings')
    api_id = models.CharField(max_length=255, help_text='API ID от Telegram')
    api_hash = models.CharField(max_length=255, help_text='API Hash от Telegram')
    session_file = models.TextField(blank=True, null=True, help_text='Содержимое файла сессии Telethon')
    is_active = models.BooleanField(default=False, help_text='Активен ли бот для данного пользователя')

    class Meta:
        db_table = 'bot_settings'
        verbose_name = 'Настройки бота'
        verbose_name_plural = 'Настройки ботов'

    def __str__(self):
        return f"Настройки для {self.user.username}"


class Prompt(models.Model):
    """Модель для хранения системных и негативных промптов."""
    bot_settings = models.OneToOneField(BotSettings, on_delete=models.CASCADE, related_name='prompt')
    system_prompt = models.TextField(help_text='Системный промпт, сгенерированный на основе ответов пользователя')
    negative_prompt = models.TextField(blank=True, null=True, help_text='Негативный промпт (что боту нельзя делать)')
    # Поле для кастомных промптов на тарифе Enterprise
    custom_prompt = models.TextField(blank=True, null=True, help_text='Кастомный промпт (для тарифа Enterprise)')
    
    class Meta:
        db_table = 'prompts'
        verbose_name = 'Промпт'
        verbose_name_plural = 'Промпты'

    def __str__(self):
        return f"Промпт для {self.bot_settings.user.username}"


class ManagedChat(models.Model):
    """Управляемые чаты и каналы, где работает ассистент."""
    bot_settings = models.ForeignKey(BotSettings, on_delete=models.CASCADE, related_name='managed_chats')
    chat_id = models.BigIntegerField(unique=True, help_text='ID чата или канала в Telegram')
    title = models.CharField(max_length=255, help_text='Название чата')
    is_active = models.BooleanField(default=True, help_text='Включен ли мониторинг в этом чате')

    class Meta:
        db_table = 'managed_chats'
        verbose_name = 'Управляемый чат'
        verbose_name_plural = 'Управляемые чаты'
        ordering = ['title']

    def __str__(self):
        return self.title


class BotActivity(models.Model):
    """Статистика активности бота."""
    bot_settings = models.ForeignKey(BotSettings, on_delete=models.CASCADE, related_name='activity_stats')
    date = models.DateField(auto_now_add=True, help_text='Дата, за которую собрана статистика')
    messages_processed = models.PositiveIntegerField(default=0, help_text='Количество обработанных сообщений')
    # Можно добавить другие поля, например, самые популярные темы (потребуется интеграция с NLP)
    most_frequent_topic = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'bot_activity'
        verbose_name = 'Активность бота'
        verbose_name_plural = 'Статистика активности'
        unique_together = ('bot_settings', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"Активность {self.bot_settings.user.username} за {self.date}"
