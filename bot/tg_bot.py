import asyncio
import traceback

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from bot.config_data.config import Config, load_config
from bot.handlers import handlers
import aiohttp



CUSTOM_SERVER = TelegramAPIServer.from_base("https://flat-union-9e75.nickprok2005.workers.dev")

async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)

config: Config = load_config()
url = f"https://flat-union-9e75.nickprok2005.workers.dev/bot{config.tg_bot.token[:5]}/getMe"

async def check_network():

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                print(f"Статус проверки сети: {response.status}")
                print(await response.text())
        except Exception as e:
            print(f"Ошибка сети в коде: {e}")



async def start_bot():
    config: Config = load_config()
    print(f"Загружен токен: {config.tg_bot.token[:5]}...***")

    bot = Bot(token=config.tg_bot.token)
    bot.session._api_server = CUSTOM_SERVER


    dp = Dispatcher()
    dp.include_router(handlers.router)

    try:
        print("Пробую подключиться к Telegram...")
        me = await bot.get_me()
        print(f"Бот подключен: @{me.username}")

        await set_main_menu(bot)

        await bot.delete_webhook(drop_pending_updates=True)

        print("Бот запущен и слушает сообщения...")
        await dp.start_polling(bot)

    finally:
        await bot.session.close()




async def main():
    while True:
        try:
            await check_network()
            await start_bot()
        except Exception as e:
            traceback.print_exc()
            print("Повторная попытка запуска через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())