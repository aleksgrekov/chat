import asyncio
import os

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

URL = f'{os.getenv('MYCHAT_URL')}/mychat/update_telegram_id'

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет, {name}👋'
                         '\nТеперь ты сможешь получать уведомления о новых сообщениях в MyChat!'.format(
        name=message.from_user.first_name
        if message.from_user.first_name
        else message.from_user.username
    ))
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as client:
        async with client.patch(URL,
                                json={
                                    "username": message.from_user.username,
                                    "chat_id": message.chat.id
                                }
                                ) as response:

            if response.status == 200:
                await message.answer('Уведомления успешно подключены!')
            else:
                await message.answer('Ошибка!')


async def run():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(run())
