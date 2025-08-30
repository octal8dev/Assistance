from django.apps import AppConfig


class AssistanteConfig(AppConfig):
    """Конфигурация приложения для управления ассистентом."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assistante'
    verbose_name = 'AI Ассистент'
