import asyncio
import traceback
import re
import aiohttp

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from bot.config_data.config import Config, load_config
from bot.handlers import handlers

# Ссылка на воркер
WORKER_URL = "https://flat-union-9e75.nickprok2005.workers.dev"


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)


async def start_bot():
    # Хардкодим токен прямо сюда для финальной проверки, чтобы исключить config.py
    # ПОТОМ ЗАМЕНИШЬ НА: config = load_config(); token = config.tg_bot.token
    token = "8724068977:AAE24aRUaZ8QTD3yK6SXbFyKRMHqhTg6HBw"
    token = re.sub(r'[^a-zA-Z0-9:-]', '', token)  # На всякий случай

    # Вариант инициализации сервера №3 (самый стабильный)
    # Используем простую склейку строк через from_base
    custom_server = TelegramAPIServer.from_base(WORKER_URL, is_local=True)

    # Создаем сессию
    session = AiohttpSession()
    bot = Bot(token=token, session=session)
    bot.session.api_server = custom_server

    dp = Dispatcher()
    dp.include_router(handlers.router)

    try:
        print(f"--- ФИНАЛЬНЫЙ ЗАПУСК ---")
        print(f"Worker: {WORKER_URL}")

        # Проверяем get_me
        me = await bot.get_me()
        print(f"✅ Бот авторизован: @{me.username}")

        await set_main_menu(bot)
        await bot.delete_webhook(drop_pending_updates=True)

        print("🚀 Работает! Поллинг запущен...")
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


async def main():
    while True:
        try:
            await start_bot()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            # Если всё еще TypeError: BaseSession.__init__() got an unexpected keyword argument 'api_server'
            # Значит у тебя очень старая или очень странная версия aiogram.
            # В таком случае замени строку 41 и 44 на:
            # session = AiohttpSession()
            # bot = Bot(token=token, session=session)
            # bot.session.api_server = custom_server

            traceback.print_exc()
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())