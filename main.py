import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, BotCommand, ContentType
from aiogram.filters import Command
from db import create_db
from commands.subscription import (
    handle_subscription, 
    check_payment_status, 
    handle_payment_options,
    handle_card_payment,
    handle_stars_payment,
    handle_back_to_subscription,
    handle_stars_confirmation,
    handle_successful_stars_payment,
    handle_stars_payment_success
)
from commands.profile import handle_profile
from commands.start import handle_start
from config import TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

async def set_commands():
    commands = [
        BotCommand(command='subscription', description='Pay to subscription'),
        BotCommand(command='profile', description='Profile Information'),
        BotCommand(command='start', description='Start message')
    ]
    await bot.set_my_commands(commands)

async def on_startup():
    create_db()
    await set_commands()
    logging.info("The bot launched!")

# Message handlers
router.message.register(handle_start, Command("start"))
router.message.register(handle_subscription, Command("subscription"))
router.message.register(handle_profile, Command("profile"))

# Callback query handlers
router.callback_query.register(check_payment_status, F.data.startswith('check_payment_'))
router.callback_query.register(handle_payment_options, F.data.startswith('payment_options_'))
router.callback_query.register(handle_card_payment, F.data.startswith('pay_card_'))
router.callback_query.register(handle_stars_payment, F.data.startswith('pay_stars_'))
router.callback_query.register(handle_back_to_subscription, F.data == 'back_to_subscription')
router.callback_query.register(handle_stars_confirmation, F.data.startswith('confirm_stars_'))

# Payment handlers for Telegram Stars
router.pre_checkout_query.register(handle_successful_stars_payment)
router.message.register(handle_stars_payment_success, F.content_type == ContentType.SUCCESSFUL_PAYMENT)

# Include router in dispatcher
dp.include_router(router)

async def main():
    await on_startup()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
