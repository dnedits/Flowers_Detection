import asyncio
import traceback

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from bot.config_data.config import Config, load_config
from bot.handlers import handlers


WORKER_URL = "https://flat-union-9e75.nickprok2005.workers.dev"

CUSTOM_SERVER = TelegramAPIServer(
    base=f"{WORKER_URL}/bot{{token}}/{{method}}",
    file=f"{WORKER_URL}/file/bot{{token}}/{{path}}",
)


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)


async def start_bot():
    config: Config = load_config()

    session = AiohttpSession(api=CUSTOM_SERVER)

    bot = Bot(
        token=config.tg_bot.token,
        session=session
    )

    dp = Dispatcher()
    dp.include_router(handlers.router)

    try:
        print("Пробую подключиться к Telegram через Worker...")

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
            await start_bot()
        except Exception:
            print("КРИТИЧЕСКИЙ СБОЙ")
            traceback.print_exc()
            print("Повторная попытка через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())