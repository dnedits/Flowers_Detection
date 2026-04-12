import os
import uuid
from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
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
    temp_filename = None
    save_dir = "./web/static/result/bot/image/"
    os.makedirs(save_dir, exist_ok=True)

    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file_info.file_path)

        annotated_img, detections, error = detector_service.predict(photo_bytes.read())

        if error:
            raise Exception(error)

        temp_filename = os.path.join(save_dir, f"temp_{uuid.uuid4().hex}.jpg")
        annotated_img.save(temp_filename)

        if detections:
            lines = []
            for i, d in enumerate(detections):
                name = html.quote(d['class_name'])
                lines.append(f"🌸 {i + 1}. <b>{name}</b> — уверен на {d['confidence']}%")

            header = "🌺 <b>Вот что удалось разглядеть моему зелёному глазу:</b>\n\n"
            footer = "\n\n✨ Природа никогда не перестаёт удивлять, правда?"

            full_caption = header + "\n".join(lines) + footer

            if len(full_caption) > 1024:
                simple_lines = [f"🌸 {i + 1}. {d['class_name']} — {d['confidence']}%" for i, d in enumerate(detections)]
                caption = (header + "\n".join(simple_lines) + footer)[:1020] + "..."
            else:
                caption = full_caption
        else:
            caption = (
                "🍂 <b>Как тихо в саду...</b>\n\n"
                "Мне не встретилось ни одного знакомого растения на этом снимке. "
                "Возможно, объект слишком далеко или скрыт в тени? "
                "Попробуйте сделать более крупный план или поймать лучшее освещение. 🌞"
            )

        await loading_msg.delete()
        loading_msg = None

        await message.answer_photo(
            photo=FSInputFile(temp_filename),
            caption=caption,
            parse_mode="HTML"
        )

    except Exception as e:
        if loading_msg:
            await loading_msg.edit_text(
                f"🌫️ <b>Туман сомнений окутал этот снимок...</b>\n\n"
                f"Ошибка: {html.quote(str(e)[:100])}\n\n"
                f"Попробуйте прислать другое фото. Я верю, у нас получится! 📸",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"❌ Произошла ошибка: {e}")

    finally:
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)
        await state.clear()
        await message.answer(
            "🌿 Я готов вдохновляться природой вместе с вами снова!\n\n"
            "Пришлите ещё одно фото или нажмите /exit, если хотите отдохнуть. "
            "Кнопка «Начать детектирование» всегда ждёт вас здесь 👇",
            reply_markup=html_keyboard
        )