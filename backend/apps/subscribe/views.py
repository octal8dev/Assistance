from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction

from .models import SubscriptionPlan, Subscription, SubscriptionHistory
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    SubscriptionHistorySerializer,
    UserSubscriptionStatusSerializer,
)


class SubscriptionPlanListView(generics.ListAPIView):
    """Список доступных тарифных планов"""
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionPlanDetailView(generics.RetrieveAPIView):
    """Детальная информация о тарифном плане"""
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class UserSubscriptionView(generics.RetrieveAPIView):
    """Информация о подписке текущего пользователя"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Возвращает подписку пользователя или None"""
        try:
            return self.request.user.subscription
        except Subscription.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        """Возвращает информацию о подписке"""
        subscription = self.get_object()
        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        else:
            return Response({
                'detail': 'No subscription found'
            }, status=status.HTTP_404_NOT_FOUND)


class SubscriptionHistoryView(generics.ListAPIView):
    """История изменений подписки пользователя"""
    serializer_class = SubscriptionHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Возвращает историю подписки пользователя"""
        try:
            subscription = self.request.user.subscription
            return subscription.history.all()
        except Subscription.DoesNotExist:
            return SubscriptionHistory.objects.none()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def subscription_status(request):
    """Возвращает статус подписки пользователя"""
    serializer = UserSubscriptionStatusSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription(request):
    """Отменяет подписку пользователя"""
    try:
        subscription = request.user.subscription

        if not subscription.is_active:
            return Response({
                'error': 'No active subscription found'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Отменяем подписку
            subscription.cancel()

            # Записываем в историю
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action='cancelled',
                description='Subscription cancelled by user'
            )

        return Response({
            'message': 'Subscription cancelled successfully'
        }, status=status.HTTP_200_OK)

    except Subscription.DoesNotExist:
        return Response({
            'error': 'No subscription found'
        }, status=status.HTTP_404_NOT_FOUND)
