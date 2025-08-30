
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BotSettingsViewSet, ManagedChatViewSet

# Создаем роутер для автоматического построения URL-адресов для viewsets
router = DefaultRouter()
router.register(r'settings', BotSettingsViewSet, basename='bot-settings')
router.register(r'managed-chats', ManagedChatViewSet, basename='managed-chats')

urlpatterns = [
    # Включаем URL-адреса, сгенерированные роутером
    path('', include(router.urls)),
]
