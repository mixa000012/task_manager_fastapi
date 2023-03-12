import aiohttp
import requests
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram import types

async def get_button_labels(user_id: int):
    async with aiohttp.ClientSession() as session:
        url = f'http://127.0.0.1:8000/task/get_all_tags'
        params = {'user_id': user_id}
        async with session.get(url, params=params) as resp:
            button_labels = await resp.json()
    return button_labels


async def create_category(user_id: int, category_name: str):
    if not category_name:
        return 'Category name cannot be empty.'
    if len(category_name) > 20:
        return 'Category name is too long.'
    if category_name in await get_button_labels(user_id):
        return 'You already have this category'
    json_data = {'tag': category_name}

    # Send request to server
    async with aiohttp.ClientSession() as session:
        url = f'http://127.0.0.1:8000/task/create_tag?user_id={user_id}'
        async with session.post(url, json=json_data) as resp:
            if resp.status != 200:
                raise Exception(f"Error creating tag: {resp.status}")
    return None


async def send_category_keyboard(user_id: int) -> types.ReplyKeyboardMarkup:
    # Create keyboard with categories
    categories = await get_button_labels(user_id)
    buttons = [KeyboardButton(text=cat) for cat in categories]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, selective=True)
    keyboard.add(*buttons)

    # Add button to create new category
    new_category_button = KeyboardButton(text='Создать новую категорию')
    keyboard.add(new_category_button)
    delete_category_button = KeyboardButton(text='Удаление категории')
    keyboard.add(delete_category_button)
    # Add home button
    home_button = KeyboardButton(text='Home')
    keyboard.add(home_button)


    return keyboard


async def delete_category(user_id: int, category_name: str):
    response = requests.delete(f'http://127.0.0.1:8000/task/delete_tag?user_id={user_id}&tag={category_name}')


