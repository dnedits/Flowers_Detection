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

CUSTOM_SERVER = TelegramAPIServer.from_base("https://flat-union-9e75.nickprok2005.workers.dev")


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)


def get_clean_token():
    conf = load_config()
    clean_token = re.sub(r'[^a-zA-Z0-9:-]', '', conf.tg_bot.token)
    return clean_token


async def check_network(token: str):
    test_url = f"https://flat-union-9e75.nickprok2005.workers.dev/bot{token}/getMe"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_url, timeout=10) as response:
                status = response.status
                text = await response.text()
                print(f"--- ДЕБАГ СЕТИ ---")
                print(f"Статус: {status}")
                print(f"Ответ: {text}")
                print(f"------------------")
                return status == 200
        except Exception as e:
            print(f"Ошибка дебаг-сети: {e}")
            return False


async def start_bot():
    token = get_clean_token()
    print(f"--- АНАЛИЗ ТОКЕНА ---")
    print(f"Чистый токен: {token[:10]}...{token[-5:]}")
    print(f"Длина: {len(token)}")

    is_ok = await check_network(token)
    if not is_ok:
        print("❌ Сеть или токен не прошли проверку. Пробуем запустить бота всё равно...")

    session = AiohttpSession(
        api_server=CUSTOM_SERVER,
        timeout=aiohttp.ClientTimeout(total=40)
    )

    bot = Bot(token=token, session=session)
    dp = Dispatcher()
    dp.include_router(handlers.router)

    try:
        print("Пробую вызвать get_me()...")
        me = await bot.get_me()
        print(f"✅ Бот подключен: @{me.username}")

        await set_main_menu(bot)
        await bot.delete_webhook(drop_pending_updates=True)

        print("🚀 Бот запущен и слушает сообщения!")
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


async def main():
    while True:
        try:
            await start_bot()
        except Exception:
            print("--- КРИТИЧЕСКАЯ ОШИБКА ---")
            traceback.print_exc()
            print("Повторная попытка запуска через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")