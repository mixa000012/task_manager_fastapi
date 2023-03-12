import requests
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram import types

def get_button_labels(user_id: int):
    response = requests.get(f'http://127.0.0.1:8000/task/get_all_tags?user_id={user_id}')
    button_labels = response.json()
    return button_labels


async def create_category(user_id: int, category_name: str):
    if not category_name:
        return 'Category name cannot be empty.'
    if len(category_name) > 20:
        return 'Category name is too long.'
    if category_name in get_button_labels(user_id):
        return 'You already have this category'
    json_data = {'tag': category_name}

    # Send request to server
    response = requests.post(f'http://127.0.0.1:8000/task/create_tag?user_id={user_id}', json=json_data)
    if response.status_code != 200:
        return f'Could not create category: {response.text}'

    return None


async def send_category_keyboard(user_id: int) -> types.ReplyKeyboardMarkup:
    # Create keyboard with categories
    categories = get_button_labels(user_id)
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


