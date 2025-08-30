import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

logger = logging.getLogger(__name__)
User = get_user_model()

class GoogleAuthService:
    @staticmethod
    def verify_token(token: str) -> dict:
        """Проверяет токен Google ID и возвращает информацию о пользователе."""
        try:
            id_info = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            return id_info
        except ValueError as e:
            logger.error(f"Ошибка верификации токена Google: {e}")
            raise Exception(f"Невалидный токен Google: {e}")

    @staticmethod
    def get_or_create_user(user_info: dict):
        """Получает или создает пользователя на основе информации от Google."""
        email = user_info.get('email')
        if not email:
            raise Exception("Email не найден в токене Google.")

        try:
            user = User.objects.get(email=email)
            # Обновляем имя, если оно изменилось в Google
            user.first_name = user_info.get('given_name', '')
            user.last_name = user_info.get('family_name', '')
            user.save()
            return user, False
        except User.DoesNotExist:
            # Создаем нового пользователя
            username = email.split('@')[0]
            if User.objects.filter(username=username).exists():
                username = f"{username}_{User.objects.count()}"

            user = User.objects.create(
                username=username,
                email=email,
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
            return user, True

    @staticmethod
    def get_tokens_for_user(user):
        """Генерирует access и refresh токены для пользователя."""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
