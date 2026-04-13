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

# Ссылка на воркер БЕЗ слэша в конце
WORKER_URL = "https://flat-union-9e75.nickprok2005.workers.dev"


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/start', description='✨ Открыть дверь в зелёный сад'),
        BotCommand(command='/help', description='🍃 Узнать тайны и секреты моего существования'),
        BotCommand(command='/exit', description='🌸 Попрощаться и уйти в тишину до новой встречи')
    ]
    await bot.set_my_commands(main_menu_commands)


def get_clean_token():
    conf = load_config()
    # Жесткая очистка: только цифры, буквы, двоеточие и дефис
    return re.sub(r'[^a-zA-Z0-9:-]', '', conf.tg_bot.token)


async def start_bot():
    token = get_clean_token()

    # Конструируем сервер вручную, чтобы aiogram точно знала, куда и что подставлять
    # Это формат, который библиотека понимает лучше всего
    custom_server = TelegramAPIServer(
        base=f"{WORKER_URL}/bot{{token}}/{{method}}",
        file=f"{WORKER_URL}/file/bot{{token}}/{{path}}"
    )

    # Создаем сессию с кастомным сервером
    session = AiohttpSession(api_server=custom_server)

    # Инициализируем бота
    bot = Bot(token=token, session=session)

    dp = Dispatcher()
    dp.include_router(handlers.router)

    try:
        print(f"Запуск через прокси: {WORKER_URL}")

        # Проверка авторизации
        me = await bot.get_me()
        print(f"✅ Бот @{me.username} успешно авторизован!")

        await set_main_menu(bot)
        await bot.delete_webhook(drop_pending_updates=True)

        print("Бот запущен. Ожидание сообщений...")
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


async def main():
    while True:
        try:
            await start_bot()
        except Exception as e:
            print("--- ОШИБКА ЗАПУСКА ---")
            # Если видим 401, выводим токен для финальной визуальной проверки
            if "Unauthorized" in str(e):
                t = get_clean_token()
                print(f"Ошибка 401. Токен: {t[:5]}...{t[-5:]} (длина {len(t)})")

            traceback.print_exc()
            print("Повтор через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Остановка...")