import asyncio
import logging
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Message, CallbackQuery
from payments import create_payment, check_payment
from db import add_subscription, get_all_subscriptions, remove_expired_subscription, get_subscription_status
from datetime import datetime, timedelta

async def handle_subscription(message: Message):
    user_id = message.from_user.id
    
    # Check if user already has an active subscription
    subscription_date = get_subscription_status(user_id)
    
    if subscription_date:
        # Check if subscription is still active
        if isinstance(subscription_date, str):
            expiration_date = datetime.fromisoformat(subscription_date)
        else:
            expiration_date = subscription_date
            
        current_time = datetime.now()
        
        if current_time < expiration_date:
            await message.answer(f"✅ У вас уже есть активная подписка до {expiration_date.strftime('%Y-%m-%d')}!")
            return
    
    # If no active subscription, show payment options
    amount = 10
    
    pay_button = InlineKeyboardButton(text="Оплатить", callback_data=f"payment_options_{user_id}_{amount}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[pay_button]])
    await message.answer("Для оплаты подписки нажмите на кнопку ниже:", reply_markup=keyboard)

async def check_payment_status(callback_query: CallbackQuery):
    # Parse callback data: "check_payment_{user_id}_{timestamp}_{amount}"
    callback_data_parts = callback_query.data.split('_')
    
    # Reconstruct the label from parts 2 and 3 (user_id_timestamp)
    if len(callback_data_parts) >= 5:  # check_payment_{user_id}_{timestamp}_{amount}
        label = f"{callback_data_parts[2]}_{callback_data_parts[3]}"
        expected_amount = float(callback_data_parts[4])
    else:
        await callback_query.answer("Ошибка в данных платежа")
        return
    
    user_id = callback_query.from_user.id

    # Answer callback query first to remove loading state
    await callback_query.answer("Проверяем платеж...")

    print(f"Checking payment for label: {label}, expected amount: {expected_amount}")
    payment_successful = check_payment(label, expected_amount)

    if payment_successful:
        expiration_date = datetime.now() + timedelta(days=30)
        
        add_subscription(user_id, expiration_date.strftime("%Y-%m-%d"))
        
        await callback_query.message.edit_text(
            f"✅ Платеж успешно обработан! Ваша подписка активна до {expiration_date.strftime('%Y-%m-%d')}."
        )
    else:
        await callback_query.message.answer(
            "❌ Платеж не найден. Убедитесь, что оплата прошла успешно, и попробуйте снова через несколько минут."
        )

async def check_subscriptions_daily(bot):
    """Check and notify about expired subscriptions daily"""
    while True:
        try:
            current_time = datetime.now()
            expired_subscriptions = get_all_subscriptions()
            
            for user_id, expiration_date in expired_subscriptions:
                if isinstance(expiration_date, str):
                    expiration_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                
                if current_time >= expiration_date:
                    try:
                        await bot.send_message(
                            user_id, 
                            "⚠️ Your subscription has expired! Use /subscription to renew."
                        )
                        remove_expired_subscription(user_id)
                        logging.info(f"Notified user {user_id} about expired subscription")
                    except Exception as e:
                        logging.error(f"Failed to notify user {user_id}: {e}")
                        
        except Exception as e:
            logging.error(f"Error in subscription check: {e}")
        
        # Wait 24 hours
        await asyncio.sleep(24 * 60 * 60)

def start_subscription_checker(bot):
    """Start the subscription checker"""
    asyncio.create_task(check_subscriptions_daily(bot))
    logging.info("Subscription checker started")

async def handle_payment_options(callback_query: CallbackQuery):
    """Handle payment method selection"""
    callback_data_parts = callback_query.data.split('_')
    
    if len(callback_data_parts) >= 4:  # payment_options_{user_id}_{amount}
        user_id = callback_data_parts[2]
        amount = float(callback_data_parts[3])
    else:
        await callback_query.answer("Ошибка в данных")
        return
    
    # Answer callback query first
    await callback_query.answer()
    
    # Create buttons for payment methods
    card_button = InlineKeyboardButton(text="💳 Картой (ЮKassa)", callback_data=f"pay_card_{user_id}_{amount}")
    stars_button = InlineKeyboardButton(text="⭐ Звездами Telegram", callback_data=f"pay_stars_{user_id}_{amount}")
    back_button = InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_subscription")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[card_button], [stars_button], [back_button]])
    
    await callback_query.message.edit_text(
        "Выберите способ оплаты подписки:",
        reply_markup=keyboard
    )

async def handle_card_payment(callback_query: CallbackQuery):
    """Handle card payment via YooKassa"""
    callback_data_parts = callback_query.data.split('_')
    
    if len(callback_data_parts) >= 4:  # pay_card_{user_id}_{amount}
        user_id = int(callback_data_parts[2])
        amount = float(callback_data_parts[3])
    else:
        await callback_query.answer("Ошибка в данных")
        return
    
    # Answer callback query first
    await callback_query.answer()
    
    # Create YooMoney payment
    payment_url, label = create_payment(user_id, amount)
    
    pay_button = InlineKeyboardButton(text="💳 Оплатить картой", url=payment_url)
    check_button = InlineKeyboardButton(text=f"✅ Я оплатил {amount} ₽", callback_data=f"check_payment_{label}_{amount}")
    back_button = InlineKeyboardButton(text="◀️ Назад", callback_data=f"payment_options_{user_id}_{amount}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[pay_button], [check_button], [back_button]])
    
    await callback_query.message.edit_text(
        f"Оплата картой через ЮKassa\n\nСумма: {amount} ₽\n\nНажмите кнопку для оплаты, затем вернитесь и нажмите 'Я оплатил':",
        reply_markup=keyboard
    )

async def handle_stars_payment(callback_query: CallbackQuery):
    """Handle payment via Telegram Stars"""
    callback_data_parts = callback_query.data.split('_')
    
    if len(callback_data_parts) >= 4:  # pay_stars_{user_id}_{amount}
        user_id = int(callback_data_parts[2])
        amount = float(callback_data_parts[3])
    else:
        await callback_query.answer("Ошибка в данных")
        return
    
    # Answer callback query first
    await callback_query.answer()
    
    # Calculate stars amount (1 star = 1 ruble approximately)
    stars_amount = int(amount)
    
    confirm_button = InlineKeyboardButton(text=f"⭐ Оплатить {stars_amount} звезд", callback_data=f"confirm_stars_{user_id}_{stars_amount}")
    back_button = InlineKeyboardButton(text="◀️ Назад", callback_data=f"payment_options_{user_id}_{amount}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[confirm_button], [back_button]])
    
    await callback_query.message.edit_text(
        f"Оплата звездами Telegram\n\nСумма: {stars_amount} ⭐\n\nНажмите кнопку для оплаты:",
        reply_markup=keyboard
    )

async def handle_back_to_subscription(callback_query: CallbackQuery):
    """Handle back to subscription menu"""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    amount = 10
    
    pay_button = InlineKeyboardButton(text="Оплатить", callback_data=f"payment_options_{user_id}_{amount}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[pay_button]])
    
    await callback_query.message.edit_text(
        "Для оплаты подписки нажмите на кнопку ниже:",
        reply_markup=keyboard
    )

async def handle_stars_confirmation(callback_query: CallbackQuery):
    """Handle stars payment confirmation"""
    callback_data_parts = callback_query.data.split('_')
    
    if len(callback_data_parts) >= 4:  # confirm_stars_{user_id}_{stars_amount}
        user_id = int(callback_data_parts[2])
        stars_amount = int(callback_data_parts[3])
    else:
        await callback_query.answer("Ошибка в данных")
        return
    
    # Answer callback query first
    await callback_query.answer()
    
    try:
        # Create invoice for Telegram Stars
        prices = [LabeledPrice(label="Подписка на 30 дней", amount=stars_amount)]
        
        # Send invoice for stars payment
        await callback_query.bot.send_invoice(
            chat_id=callback_query.from_user.id,
            title="Подписка на бота",
            description="Подписка на бота на 30 дней",
            payload=f"subscription_{user_id}_{stars_amount}",
            provider_token="",  # Empty for Telegram Stars
            currency="XTR",  # Telegram Stars currency
            prices=prices,
            start_parameter="subscription",
        )
        
        await callback_query.message.edit_text(
            "Счет на оплату звездами отправлен. Пожалуйста, оплатите его для активации подписки."
        )
        
    except Exception as e:
        print(f"Error creating stars invoice: {e}")
        await callback_query.message.edit_text(
            "Произошла ошибка при создании счета. Попробуйте еще раз или выберите другой способ оплаты."
        )

async def handle_successful_stars_payment(pre_checkout_query):
    """Handle pre-checkout query for stars payment"""
    await pre_checkout_query.answer(ok=True)

async def handle_stars_payment_success(message: Message):
    """Handle successful stars payment"""
    if message.successful_payment:
        # Parse payload to get user info
        payload_parts = message.successful_payment.invoice_payload.split('_')
        
        if len(payload_parts) >= 3 and payload_parts[0] == "subscription":
            user_id = int(payload_parts[1])
            stars_amount = int(payload_parts[2])
            
            # Add subscription
            expiration_date = datetime.now() + timedelta(days=30)
            add_subscription(user_id, expiration_date.strftime("%Y-%m-%d"))
            
            await message.answer(
                f"✅ Оплата звездами успешно обработана! Ваша подписка активна до {expiration_date.strftime('%Y-%m-%d')}."
            )
        else:
            await message.answer("Ошибка в обработке платежа.")
