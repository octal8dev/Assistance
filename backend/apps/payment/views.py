import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    StripeCheckoutSessionSerializer, # Note: This serializer is used for YooMoney as well
)
# from .services import StripeService # Stripe is disabled
from .services import YooMoneyService, PaymentService, WebhookService
from apps.subscribe.models import SubscriptionPlan


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    """Создает сессию для оплаты подписки (только YooMoney)"""
    serializer = PaymentCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                plan_id = serializer.validated_data['subscription_plan_id']
                plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
                
                # Создаем платеж и подписку, метод оплаты по умолчанию 'yoomoney'
                payment, subscription = PaymentService.create_subscription_payment(
                    request.user, plan
                )
                
                success_url = serializer.validated_data.get('success_url', f"{settings.FRONTEND_URL}/payment/success")
                cancel_url = serializer.validated_data.get('cancel_url', f"{settings.FRONTEND_URL}/payment/cancel")
                
                # Создаем платеж в YooMoney
                session_data = YooMoneyService.create_payment(
                    payment, success_url, cancel_url
                )
                
                if session_data:
                    response_serializer = StripeCheckoutSessionSerializer(session_data)
                    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({'error': 'Failed to create YooMoney payment session'}, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@require_POST
def yoomoney_webhook(request):
    """Webhook endpoint для YooMoney. Принимает application/x-www-form-urlencoded"""
    try:
        # YooMoney sends data in a form-urlencoded POST request
        data = request.POST.dict()
        success = WebhookService.process_yoomoney_webhook(data)
        if success:
            return HttpResponse(status=200)
        return HttpResponse(status=400, content='Webhook processing failed.')
    except Exception:
        return HttpResponse(status=400, content='Invalid webhook request.')

# import stripe # Stripe is disabled
# @csrf_exempt
# @require_POST
# def stripe_webhook(request):
#     """Webhook endpoint для Stripe (отключен)"""
#     payload = request.body
#     sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
#     
#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
#         )
#     except (ValueError, stripe.error.SignatureVerificationError):
#         return HttpResponse(status=400)
#     
#     success = WebhookService.process_stripe_webhook(event)
#     if success:
#         return HttpResponse(status=200)
#     return HttpResponse(status=400)
