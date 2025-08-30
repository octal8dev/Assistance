
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Кастомное право доступа, которое разрешает доступ только владельцу объекта.
    Предполагается, что у модели есть поле `user`.
    """
    def has_object_permission(self, request, view, obj):
        # Для настроек бота, проверяем obj.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Для связанных объектов (например, Prompt), проверяем через bot_settings
        if hasattr(obj, 'bot_settings'):
            return obj.bot_settings.user == request.user
        return False
