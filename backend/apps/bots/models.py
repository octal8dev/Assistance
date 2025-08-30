from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Chat(models.Model):
    """Модель для хранения информации о чатах/группах в Telegram."""
    chat_id = models.BigIntegerField(unique=True, help_text="Уникальный идентификатор чата в Telegram")
    name = models.CharField(max_length=255, help_text="Название чата/группы")

    def __str__(self):
        return f'{self.name} ({self.chat_id})'

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"


class Bot(models.Model):
    """Модель для хранения информации о телеграм-боте."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bots',
        verbose_name="Владелец бота"
    )
    name = models.CharField(max_length=255, verbose_name="Имя бота")
    api_id = models.CharField(max_length=255, verbose_name="API ID")
    api_hash = models.CharField(max_length=255, verbose_name="API Hash")
    is_active = models.BooleanField(default=False, verbose_name="Активен")
    chats = models.ManyToManyField(
        'Chat',
        related_name='bots',
        blank=True,
        verbose_name="Чаты для работы"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Бот"
        verbose_name_plural = "Боты"


class Session(models.Model):
    """Модель для хранения сессионных данных Telethon."""
    bot = models.OneToOneField(
        Bot,
        on_delete=models.CASCADE,
        related_name='session',
        verbose_name="Бот"
    )
    session_data = models.TextField(verbose_name="Данные сессии")

    def __str__(self):
        return f"Сессия для {self.bot.name}"

    class Meta:
        verbose_name = "Сессия"
        verbose_name_plural = "Сессии"
