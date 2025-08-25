from aiogram.types import Message
from db import get_subscription_status
from datetime import datetime

async def handle_profile(message: Message):
    user_id = message.from_user.id
    subscription_status = get_subscription_status(user_id)
    
    if subscription_status:
        # Handle both string and datetime objects
        if isinstance(subscription_status, str):
            # If it's a string, parse it to datetime
            expiration_date_obj = datetime.fromisoformat(subscription_status.replace('Z', '+00:00') if 'Z' in subscription_status else subscription_status)
            expiration_date = expiration_date_obj.strftime("%Y-%m-%d")
        else:
            # If it's a datetime object, format it
            expiration_date_obj = subscription_status
            expiration_date = subscription_status.strftime("%Y-%m-%d")
        
        # Check if subscription is still active
        current_time = datetime.now()
        if current_time < expiration_date_obj:
            status_text = f"✅ Ваша подписка активна до: {expiration_date}"
        else:
            status_text = "❌ Ваша подписка истекла. Используйте /subscription для продления."
    else:
        status_text = "❌ Подписка не активна. Используйте /subscription для оформления."

    profile_message = f"👤 Профиль пользователя:\n🆔 ID: {user_id}\n{status_text}"
    await message.answer(profile_message)
