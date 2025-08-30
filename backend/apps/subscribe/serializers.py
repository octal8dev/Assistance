from rest_framework import serializers
from django.utils import timezone
from .models import SubscriptionPlan, Subscription, SubscriptionHistory


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Сериализатор для тарифных планов"""

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'price', 'duration_days', 'features',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        '''Переопределение для гарантии корректного вывода'''
        data = super().to_representation(instance)

        # Убедиться, что feauters - это объект
        if not data.get('features'):
            data['features'] = {}

        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки"""
    plan_info = SubscriptionPlanSerializer(source='plan', read_only=True)
    user_info = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_info', 'plan', 'plan_info', 'status',
            'start_date', 'end_date', 'auto_renew', 'is_active',
            'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'start_date', 'end_date',
            'created_at', 'updated_at'
        ]

    def get_user_info(self, obj):
        """Возвращает информацию о пользователе"""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.full_name,
            'email': obj.user.email,
        }


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки"""

    class Meta:
        model = Subscription
        fields = ['plan']

    def validate_plan(self, value):
        '''Валидация тарифного плана'''
        if not value.is_active:
            raise serializers.ValidationError('Selected plan is not active.')
        return value

    def validate(self, attrs):
        '''Общая валидация'''
        user = self.context['request'].user

        # Проверяем, есть ли уже активная подписка
        if hasattr(user, 'subscription') and user.subscription.is_active():
            raise serializers.ValidationError({
                'non_field_errors': ['User already has an active subscription.']
            })

        return attrs

    def create(self, validated_data):
        """Создает подписку"""
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'pending'
        validated_data['start_date'] = timezone.now()
        validated_data['end_date'] = timezone.now()
        return super().create(validated_data)


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для истории подписки"""

    class Meta:
        model = SubscriptionHistory
        fields = [
            'id', 'action', 'description', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserSubscriptionStatusSerializer(serializers.Serializer):
    """Сериализатор для статуса подписки пользователя"""
    has_subscription = serializers.BooleanField()
    is_active = serializers.BooleanField()
    subscription = SubscriptionSerializer(allow_null=True)

    def to_representation(self, instance):
        """Формирует ответ с информацией о подписке пользователя"""
        user = instance
        has_subscription = hasattr(user, 'subscription')
        subscription = user.subscription if has_subscription else None
        is_active = subscription.is_active if subscription else False

        return {
            'has_subscription': has_subscription,
            'is_active': is_active,
            'subscription': SubscriptionSerializer(subscription).data if subscription else None,
        }
