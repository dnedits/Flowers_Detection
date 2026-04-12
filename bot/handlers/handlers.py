import os
import uuid
import io  # Добавлено для работы с байтами в памяти
from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile  # Используем буфер вместо записи на диск
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.detector import detector_service
from bot.keyboards.keyboard import html_keyboard, remove_keyboard
from bot.lexicon.lexicon import LEXICON_RU

router = Router()


class FileState(StatesGroup):
    photo = State()


@router.message(Command(commands=['start']))
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"<b>🌿 Добро пожаловать в зелёное братство, {message.from_user.full_name}!</b> 👀",
        parse_mode="HTML"
    )
    await message.answer(
        LEXICON_RU['/start'],
        reply_markup=html_keyboard
    )


@router.message(Command(commands=["help"]))
async def help_command(message: Message):
    await message.answer(
        text=LEXICON_RU['/help'],
        reply_markup=html_keyboard,
        parse_mode="HTML"
    )


@router.message(Command(commands=["exit"]))
async def exit_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"🍃 Тишина… Листья замерли в ожидании. "
        f"Когда природа снова позовёт вас в путь — просто нажмите /start, и я буду здесь, чтобы помочь. "
        f"До новых зелёных встреч! 🌙",
        parse_mode="HTML"
    )


@router.message(F.text == '🍃 Приоткрыть завесу листвы')
async def get_photo(message: Message, state: FSMContext):
    await state.set_state(FileState.photo)
    await message.answer(
        '📸 Пришлите мне фотографию растения.\n\n'
        'Я всмотрюсь в каждый листочек и лепесток, чтобы раскрыть вам его имя и тайны. '
        'Жду ваш снимок! 🌱',
        reply_markup=remove_keyboard
    )


@router.message(FileState.photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    bot = message.bot
    loading_msg = await message.reply(
        "🔍 Вооружаюсь лупой и ботаническим справочником...\n\n_Это займёт всего мгновение._",
        parse_mode="Markdown"
    )

    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        img_data = photo_bytes_io.read()

        annotated_img, detections, error = detector_service.predict(img_data)

        if error:
            raise Exception(error)

        if detections:
            lines = []
            for i, d in enumerate(detections):
                name = html.quote(str(d['class_name']))
                lines.append(f"🌸 {i + 1}. <b>{name}</b> — уверен на {d['confidence']}%")

            header = "🌺 <b>Вот что удалось разглядеть моему зелёному глазу:</b>\n\n"
            footer = "\n\n✨ Природа никогда не перестаёт удивлять, правда?"
            caption = (header + "\n".join(lines) + footer)[:1024]
        else:
            caption = (
                "🍂 <b>Как тихо в саду...</b>\n\n"
                "Мне не встретилось ни одного знакомого растения на этом снимке. "
                "Попробуйте сделать более крупный план или поймать лучшее освещение. 🌞"
            )

        output_buffer = io.BytesIO()
        annotated_img.save(output_buffer, format="JPEG")
        output_buffer.seek(0)

        photo_to_send = BufferedInputFile(output_buffer.read(), filename="result.jpg")

        await loading_msg.delete()
        await message.answer_photo(
            photo=photo_to_send,
            caption=caption,
            parse_mode="HTML"
        )

    except Exception as e:
        error_text = f"🌫️ <b>Туман сомнений окутал этот снимок...</b>\n\nОшибка: {html.quote(str(e)[:100])}"
        if loading_msg:
            await loading_msg.edit_text(error_text, parse_mode="HTML")
        else:
            await message.answer(error_text, parse_mode="HTML")

    finally:
        await state.clear()
        await message.answer(
            "🌿 Я готов вдохновляться природой снова!\n\n"
            "Пришлите фото или нажмите /exit.",
            reply_markup=html_keyboard
        )