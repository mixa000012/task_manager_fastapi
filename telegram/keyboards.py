from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import KeyboardButton
from aiogram.types import ReplyKeyboardMarkup

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
main_keyboard.add(
    KeyboardButton("Создать таск"),
    KeyboardButton("Категории"),
    KeyboardButton("Все задачи"),
)

# # Define the keyboard for the categories menu
# categories_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
# categories_keyboard.add(
#     KeyboardButton('Home')
# )

# Define the keyboard for the tasks menu
# tasks_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
# tasks_keyboard.add(
#     KeyboardButton('Home')
# )

add_category_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="add_category:yes")],
        [InlineKeyboardButton(text="Нет", callback_data="add_category:no")],
    ]
)
