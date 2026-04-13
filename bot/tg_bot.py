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

# Ссылка на твой воркер (ВАЖНО: без /bot на конце)
WORKER_URL = "https://flat-union-9e75.nickprok2005.workers.dev"


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)


def get_clean_token():
    """Загрузка и очистка токена от невидимых символов и кавычек."""
    conf = load_config()
    token = conf.tg_bot.token
    # Оставляем только допустимые символы токена
    return re.sub(r'[^a-zA-Z0-9:-]', '', token)


async def check_network(token: str):
    """Прямая проверка связи через aiohttp."""
    test_url = f"{WORKER_URL}/bot{token}/getMe"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_url, timeout=10) as response:
                res_text = await response.text()
                print(f"--- ПРОВЕРКА СЕТИ ---")
                print(f"Статус: {response.status}")
                print(f"Ответ API: {res_text}")
                return response.status == 200
        except Exception as e:
            print(f"Сетевая ошибка: {e}")
            return False


async def start_bot():
    token = get_clean_token()

    # 1. Создаем объект сервера по твоей ссылке
    custom_server = TelegramAPIServer.from_base(WORKER_URL)

    # 2. Создаем сессию, указывая api_server (как в документации)
    # Если здесь вылетает ошибка, значит версия aiogram требует создания через пропсы
    session = AiohttpSession(api_url=custom_server)

    # 3. Инициализируем бота
    bot = Bot(token=token, session=session)

    dp = Dispatcher()
    dp.include_router(handlers.router)

    try:
        # Предварительная проверка связи
        if await check_network(token):
            print("✅ Соединение с Cloudflare установлено.")
        else:
            print("❌ Ошибка авторизации (401) или сети. Проверь токен!")

        print("Запрашиваю данные бота (get_me)...")
        me = await bot.get_me()
        print(f"🎉 Успех! Бот @{me.username} готов к работе.")

        await set_main_menu(bot)
        await bot.delete_webhook(drop_pending_updates=True)

        print("Бот запущен в режиме polling.")
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


async def main():
    while True:
        try:
            await start_bot()
        except Exception:
            print("--- КРИТИЧЕСКИЙ СБОЙ ---")
            traceback.print_exc()
            print("Перезапуск через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Завершение работы.")