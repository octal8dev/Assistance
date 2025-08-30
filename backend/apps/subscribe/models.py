from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class SubscriptionPlan(models.Model):
    """Модель тарифного плана для ассистента Octal Assistance."""
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    features = models.JSONField(default=dict, help_text="Возможности тарифного плана (например, кол-во ботов, кастомные промпты)")
    is_active = models.BooleanField(default=True, help_text="Активен ли тариф для выбора пользователями")

    class Meta:
        db_table = 'subscription_plans'
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - {self.price} руб."


class Subscription(models.Model):
    """Модель подписки пользователя на тарифный план."""
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Истекла'),
        ('cancelled', 'Отменена'),
        ('pending', 'В ожидании'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Пользователь'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscriptions',
        verbose_name='Тарифный план'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    start_date = models.DateTimeField(verbose_name='Дата начала')
    end_date = models.DateTimeField(verbose_name='Дата окончания')
    auto_renew = models.BooleanField(default=False, verbose_name='Автопродление')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date', 'status']),
        ]

    def __str__(self):
        return f"Подписка {self.user.username} на {self.plan.name} ({self.get_status_display()})"

    @property
    def is_active(self):
        """Проверяет, активна ли подписка."""
        return self.status == 'active' and self.end_date > timezone.now()

    def activate(self):
        """Активирует подписку."""
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        self.save()

    def cancel(self):
        """Отменяет подписку."""
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()

    def expire(self):
        """Помечает подписку как истекшую."""
        self.status = 'expired'
        self.save()


class SubscriptionHistory(models.Model):
    """История изменений статуса подписки."""
    ACTION_CHOICES = [
        ('created', 'Создана'),
        ('activated', 'Активирована'),
        ('renewed', 'Продлена'),
        ('cancelled', 'Отменена'),
        ('expired', 'Истекла'),
        ('payment_failed', 'Ошибка платежа'),
    ]

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Действие')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscription_history'
        verbose_name = 'История подписки'
        verbose_name_plural = 'История подписок'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subscription.user.username} - {self.get_action_display()}"
