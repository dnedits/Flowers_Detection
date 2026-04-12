from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

html_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🍃 Приоткрыть завесу листвы')]
    ],
    resize_keyboard=True,
    input_field_placeholder='📸 Пришлите фото — я всмотрюсь в каждый лепесток...'
)
remove_keyboard = ReplyKeyboardRemove()