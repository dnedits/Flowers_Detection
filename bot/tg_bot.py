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

# Ссылка на твой воркер (БЕЗ слэша в конце)
WORKER_URL = "https://flat-union-9e75.nickprok2005.workers.dev"
CUSTOM_SERVER = TelegramAPIServer.from_base(WORKER_URL)


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)


def get_clean_token():
    """Загрузка и жесткая очистка токена от кавычек и мусора."""
    conf = load_config()
    token = conf.tg_bot.token
    # Оставляем только то, что может быть в токене (цифры, буквы, двоеточие, дефис)
    return re.sub(r'[^a-zA-Z0-9:-]', '', token)


async def check_network(token: str):
    """Проверка связи через aiohttp напрямую."""
    test_url = f"{WORKER_URL}/bot{token}/getMe"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_url, timeout=15) as response:
                res_text = await response.text()
                print(f"--- ПРОВЕРКА СВЯЗИ ---")
                print(f"Статус: {response.status}")
                print(f"Ответ ТГ: {res_text}")
                return response.status == 200
        except Exception as e:
            print(f"Ошибка сети: {e}")
            return False


async def start_bot():
    token = get_clean_token()

    # 1. Создаем сессию БЕЗ аргументов в конструкторе (чтобы не было TypeError)
    session = AiohttpSession()

    # 2. Вручную подменяем сервер API внутри сессии
    session.api_server = CUSTOM_SERVER

    # 3. Инициализируем бота с этой сессией
    bot = Bot(token=token, session=session)

    dp = Dispatcher()
    dp.include_router(handlers.router)

    try:
        # Сначала проверяем сеть простым запросом
        if await check_network(token):
            print("✅ Сетевой мост через Cloudflare работает!")
        else:
            print("⚠️ Проверка сети не прошла, но пробуем запустить бота...")

        print("Запрашиваю get_me()...")
        me = await bot.get_me()
        print(f"🚀 Успех! Бот @{me.username} на связи.")

        await set_main_menu(bot)
        await bot.delete_webhook(drop_pending_updates=True)

        print("Бот запущен. Жду сообщений...")
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


async def main():
    while True:
        try:
            await start_bot()
        except Exception:
            print("--- ОШИБКА ЗАПУСКА ---")
            traceback.print_exc()
            print("Перезапуск через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Выход...")