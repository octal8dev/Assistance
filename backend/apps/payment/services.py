import logging
from django.conf import settings
from django.utils import timezone
from yoomoney import Client, Quickpay
from typing import Dict, Optional, Tuple

from .models import Payment, WebhookEvent
from apps.subscribe.models import Subscription, SubscriptionPlan, SubscriptionHistory

# import stripe # Stripe is disabled

logger = logging.getLogger(__name__)

# Stripe API key (disabled)
# stripe.api_key = settings.STRIPE_SECRET_KEY

# YooMoney setup
yoomoney_client = Client(settings.YOOMONEY_TOKEN)

class YooMoneyService:
    """Service for handling YooMoney payments."""

    @staticmethod
    def create_payment(payment: Payment, success_url: str, cancel_url: str) -> Optional[Dict]:
        """Creates a YooMoney payment and returns the checkout URL."""
        try:
            quickpay = Quickpay(
                receiver=settings.YOOMONEY_RECEIVER,
                quickpay_form='shop',
                targets=f'Payment for subscription #{payment.subscription.id}',
                paymentType='SB',
                sum=payment.amount,
                label=str(payment.id), # Label must be a string
                success_url=success_url
            )

            payment.yoomoney_payment_id = quickpay.label # Save the label for reference
            payment.status = 'processing'
            payment.save()

            return {
                'checkout_url': quickpay.redirected_url,
                'session_id': quickpay.label, # Using label as a session identifier
                'payment_id': payment.id
            }
        except Exception as e:
            logger.error(f"Error creating YooMoney payment: {e}")
            payment.mark_as_failed(str(e))
            return None

# class StripeService: (Stripe is disabled)
#     """Service for handling Stripe payments."""

#     @staticmethod
#     def create_checkout_session(payment: Payment, success_url: str, cancel_url: str) -> Optional[Dict]:
#         """Creates a Stripe Checkout session."""
#         # ... (Stripe logic is commented out)

class PaymentService:
    """Main service for handling payments."""

    @staticmethod
    def create_subscription_payment(user, plan: SubscriptionPlan) -> Tuple[Payment, Subscription]:
        """Creates a payment and subscription, with 'yoomoney' as the default payment method."""
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status='pending',
            start_date=timezone.now(),
            end_date=timezone.now() # Will be updated upon successful payment
        )

        payment = Payment.objects.create(
            user=user,
            subscription=subscription,
            amount=plan.price,
            currency='RUB', # YooMoney works with RUB
            description=f'Subscription to {plan.name}',
            payment_method='yoomoney' # Default to yoomoney
        )

        SubscriptionHistory.objects.create(
            subscription=subscription,
            action='created',
            description=f'Subscription created for plan {plan.name}'
        )

        return payment, subscription

    @staticmethod
    def process_successful_payment(payment: Payment) -> bool:
        """Handles a successful payment."""
        try:
            payment.mark_as_succeeded()
            if payment.subscription:
                payment.subscription.activate()
                SubscriptionHistory.objects.create(
                    subscription=payment.subscription,
                    action='activated',
                    description='Subscription activated after successful payment',
                    metadata={'payment_id': payment.id}
                )
            logger.info(f"Payment {payment.id} processed successfully")
            return True
        except Exception as e:
            logger.error(f"Error processing successful payment {payment.id}: {e}")
            return False

    @staticmethod
    def process_failed_payment(payment: Payment, reason: str) -> bool:
        """Handles a failed payment."""
        try:
            payment.mark_as_failed(reason)
            if payment.subscription:
                payment.subscription.cancel()
                SubscriptionHistory.objects.create(
                    subscription=payment.subscription,
                    action='cancelled',
                    description=f'Subscription cancelled due to failed payment: {reason}',
                    metadata={'payment_id': payment.id}
                )
            logger.warning(f"Payment {payment.id} failed: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error processing failed payment {payment.id}: {e}")
            return False

class WebhookService:
    """Service for handling webhook events."""

    @staticmethod
    def process_yoomoney_webhook(event_data: Dict) -> bool:
        """Processes a YooMoney webhook notification."""
        try:
            # Construct a unique event ID
            event_id = event_data.get('notification_type') + '_' + event_data.get('operation_id', 'na')
            
            if WebhookEvent.objects.filter(provider='yoomoney', event_id=event_id).exists():
                return True # Event already processed

            webhook_event = WebhookEvent.objects.create(
                provider='yoomoney',
                event_id=event_id,
                event_type=event_data.get('notification_type'),
                data=event_data
            )

            success = WebhookService._handle_yoomoney_notification(event_data)

            if success:
                webhook_event.mark_as_processed()
            else:
                webhook_event.mark_as_failed("Processing logic failed")

            return success
        except Exception as e:
            logger.error(f"Error processing YooMoney webhook: {e}")
            return False

    @staticmethod
    def _handle_yoomoney_notification(event_data: Dict) -> bool:
        """Handles the logic for a YooMoney notification."""
        try:
            payment_id = event_data.get('label')
            if not payment_id:
                logger.warning("No 'label' (payment_id) in YooMoney notification.")
                return False

            payment = Payment.objects.get(id=int(payment_id))

            # Check the hash to verify the notification
            notification_secret = settings.YOOMONEY_WEBHOOK_SECRET
            # sha1_hash = notification_type&operation_id&amount&currency&datetime&sender&codepro&notification_secret&label
            hash_string = f"{event_data.get('notification_type', '')}&{event_data.get('operation_id', '')}&{event_data.get('amount', '')}&{event_data.get('currency', '')}&{event_data.get('datetime', '')}&{event_data.get('sender', '')}&{event_data.get('codepro', '')}&{notification_secret}&{event_data.get('label', '')}"
            
            import hashlib
            calculated_hash = hashlib.sha1(hash_string.encode('utf-8')).hexdigest()

            if calculated_hash != event_data.get('sha1_hash'):
                logger.error("YooMoney webhook hash mismatch!")
                return False
            
            if event_data.get('unaccepted') == 'true':
                return PaymentService.process_failed_payment(payment, 'YooMoney payment was unaccepted.')

            return PaymentService.process_successful_payment(payment)

        except Payment.DoesNotExist:
            logger.error(f"Payment with ID {payment_id} not found for YooMoney notification.")
            return False
        except Exception as e:
            logger.error(f"Error in _handle_yoomoney_notification: {e}")
            return False

    # @staticmethod (Stripe webhook processing is disabled)
    # def process_stripe_webhook(event_data: Dict) -> bool:
    #     # ... (Stripe webhook logic is commented out)
