import aiohttp
import requests
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from decouple import config

task_url = config('API_ROUT')


async def get_button_labels(user_id: int):
    async with aiohttp.ClientSession() as session:
        url = f'{task_url}/get_all_tags'
        params = {'user_id': user_id}
        async with session.get(url, params=params) as resp:
            button_labels = await resp.json()
    return button_labels


async def create_category(user_id: int, category_name: str):
    if category_name in ['Удаление категории', 'Создать новую категорию', 'Home']:
        return 'Недопустимое название категории'
    if not category_name:
        return 'Category name cannot be empty.'
    if len(category_name) > 20:
        return 'Category name is too long.'
    if category_name in await get_button_labels(user_id):
        return 'You already have this category'
    json_data = {'tag': category_name, 'userd_id': user_id}

    # Send request to server
    async with aiohttp.ClientSession() as session:
        url = f'{task_url}/create_tag'
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
    response = requests.delete(f'{task_url}/delete_tag?user_id={user_id}&tag={category_name}')


async def get_all_tasks(chat_id, bot, message_id=None, user_id=None, chat_type=None, tag=None):
    url = f'{task_url}/get_all_tasks?user_id={user_id}'
    if tag is not None:
        url += f'&tag={tag}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            tasks = await resp.json()
    if len(tasks) > 0:
        buttons = [
            [InlineKeyboardButton(text=task.get('title'), callback_data=f"delete_task:{task.get('id')}:{tag}")]
            for task in tasks
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        if chat_type == 'private':
            await bot.send_message(chat_id, 'Ваши задачи', reply_markup=keyboard)
        elif message_id:
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
        else:
            await bot.send_message(chat_id, 'Ваши задачи', reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, 'У вас нет задач')
