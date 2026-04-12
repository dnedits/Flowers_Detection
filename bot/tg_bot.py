import asyncio
import traceback

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.session.aiohttp import AiohttpSession

from config_data.config import Config, load_config
from handlers import handlers


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)


async def start_bot():
    config: Config = load_config()

    session = AiohttpSession()

    bot = Bot(
        token=config.tg_bot.token,
        session=session
    )

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
            await start_bot()
        except Exception as e:
            traceback.print_exc()
            print("Повторная попытка запуска через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())