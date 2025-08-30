
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import BotSettings, ManagedChat
from .serializers import BotSettingsSerializer, ManagedChatSerializer
from apps.main.permissions import IsOwner # Импортируем кастомные права

class BotSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления настройками бота.
    Позволяет пользователю создавать, просматривать и обновлять свои настройки.
    Удаление настроек не предполагается через API, только деактивация.
    """
    serializer_class = BotSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Возвращает настройки только для текущего пользователя."""
        return BotSettings.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Привязывает создаваемые настройки к текущему пользователю."""
        serializer.save(user=self.request.user)

    def get_object(self):
        """
        Возвращает единственный объект настроек для пользователя.
        Перехватываем стандартный get_object, чтобы всегда возвращать
        объект, связанный с пользователем, без необходимости указывать id в URL.
        """
        obj = BotSettings.objects.filter(user=self.request.user).first()
        self.check_object_permissions(self.request, obj)
        return obj

class ManagedChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления отслеживаемыми чатами.
    Позволяет только обновлять (активировать/деактивировать) и получать список.
    Добавление и удаление чатов происходит автоматически на стороне бота.
    """
    serializer_class = ManagedChatSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    # Разрешаем только GET и PATCH
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        """
        Возвращает чаты, связанные с настройками текущего пользователя.
        """
        user = self.request.user
        if hasattr(user, 'bot_settings'):
            return ManagedChat.objects.filter(bot_settings=user.bot_settings)
        return ManagedChat.objects.none() # Возвращаем пустой queryset, если настроек нет
