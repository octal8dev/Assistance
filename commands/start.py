from aiogram.types import Message

async def handle_start(message: Message):
    start_message = f"Hi! Use: \n/subscription"
    await message.answer(start_message)
