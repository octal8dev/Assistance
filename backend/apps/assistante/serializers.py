
from rest_framework import serializers
from .models import BotSettings, Prompt, BotActivity, ManagedChat

class BotActivitySerializer(serializers.ModelSerializer):
    """Сериализатор для статистики активности бота."""
    class Meta:
        model = BotActivity
        fields = ['date', 'messages_processed', 'most_frequent_topic']

class PromptSerializer(serializers.ModelSerializer):
    """Сериализатор для промптов."""
    class Meta:
        model = Prompt
        # Исключаем bot_settings, так как он будет связан автоматически
        exclude = ['bot_settings']

class ManagedChatSerializer(serializers.ModelSerializer):
    """Сериализатор для управляемых чатов."""
    class Meta:
        model = ManagedChat
        fields = ['id', 'chat_id', 'title', 'is_active']
        read_only_fields = ['id', 'chat_id', 'title']

class BotSettingsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для настроек бота.
    Включает вложенные сериализаторы для промптов и статистики.
    """
    prompt = PromptSerializer()
    activity_stats = BotActivitySerializer(many=True, read_only=True)
    managed_chats = ManagedChatSerializer(many=True, read_only=True)

    class Meta:
        model = BotSettings
        fields = [
            'id',
            'api_id',
            'api_hash',
            'is_active',
            'prompt',
            'managed_chats',
            'activity_stats',
        ]
        # api_id и api_hash можно будет задать один раз, но не изменять через API
        # чтобы избежать случайной перезаписи. Для смены ключей потребуется другой процесс.
        extra_kwargs = {
            'api_id': {'write_only': True},
            'api_hash': {'write_only': True},
        }

    def update(self, instance, validated_data):
        # Обработка вложенного сериализатора для Prompt
        prompt_data = validated_data.pop('prompt', None)
        if prompt_data:
            prompt_instance = getattr(instance, 'prompt', None)
            if prompt_instance:
                prompt_serializer = self.fields['prompt']
                prompt_serializer.update(prompt_instance, prompt_data)

        # Обновление основной модели BotSettings
        instance = super().update(instance, validated_data)
        return instance

    def create(self, validated_data):
        # Устанавливаем пользователя из запроса
        validated_data['user'] = self.context['request'].user
        
        prompt_data = validated_data.pop('prompt')
        
        # Создаем экземпляр BotSettings
        bot_settings = BotSettings.objects.create(**validated_data)
        
        # Создаем связанный Prompt
        Prompt.objects.create(bot_settings=bot_settings, **prompt_data)
        
        return bot_settings
