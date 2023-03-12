# -*- coding: utf-8 -*-
import logging

import aiohttp
import requests
from decouple import config
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from function import create_category, get_button_labels, send_category_keyboard, delete_category

API_TOKEN = config('API_TOKEN')
storage = MemoryStorage()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Define the keyboard for the main menu
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
main_keyboard.add(
    KeyboardButton('Создать таск'),
    KeyboardButton('Категории'),
    KeyboardButton('Все задачи')
)

# Define the keyboard for the categories menu
categories_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
categories_keyboard.add(
    KeyboardButton('Home')
)

# Define the keyboard for the tasks menu
tasks_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
tasks_keyboard.add(
    KeyboardButton('Home')
)

add_category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data="add_category:yes")],
    [InlineKeyboardButton(text="Нет", callback_data="add_category:no")]
])


async def get_all_tasks(chat_id, message_id=None, user_id=None, chat_type=None, tag=None):
    url = f'http://127.0.0.1:8000/task/get_all_tasks?user_id={user_id}'
    if tag is not None:
        url += f'&tag={tag}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            tasks = await resp.json()

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


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Привет! Я помогу тебе управлять своими задачами. Нажми на кнопку, чтобы начать",
                         reply_markup=main_keyboard)


@dp.message_handler(lambda message: message.text in ['Создать таск', 'Категории', 'Все задачи'])
async def main_menu_handler(message: types.Message, state: FSMContext):
    if message.text == 'Создать таск':
        await message.answer("Введите описание таска:")
        await state.set_state("waiting_for_task_description")

    elif message.text == 'Категории':
        keyboard = await send_category_keyboard(message.from_user.id)
        await bot.send_message(chat_id=message.chat.id, text="Выберете категорию:", reply_markup=keyboard)

    elif message.text == 'Все задачи':
        await get_all_tasks(chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id,
                            chat_type=message.chat.type)


@dp.message_handler(lambda message: message.text == 'Home')
async def home_button_handler(message: types.Message):
    await message.answer("Главное меню", reply_markup=main_keyboard)


class CreateTask(StatesGroup):
    waiting_for_task_description = State()
    waiting_for_add_category = State()
    waiting_for_category_name = State()
    waiting_for_category_selection = State()


class CreateCategory(StatesGroup):
    name = State()

def get_buttons(user_id: int):
    url = f'http://127.0.0.1:8000/task/get_all_tags'
    params = {'user_id': user_id}
    button_labels = requests.get(url, params=params).json()
    return button_labels
@dp.message_handler(lambda message: message.text in get_buttons(message.from_user.id))
async def handle_category_click_wrapper(message: types.Message):
    await handle_category_click(message)


async def handle_category_click(message: types.Message):
    tag = message.text
    await get_all_tasks(chat_id=message.chat.id, message_id=message.message_id, user_id=message.from_user.id, tag=tag,
                        chat_type=message.chat.type)


@dp.message_handler(lambda message: message.text == 'Создать новую категорию', state=None)
async def create_category_handler(message: types.Message):
    await message.answer('Введите название новой категории:')
    await CreateCategory.name.set()


@dp.message_handler(state=CreateCategory.name)
async def process_create_category(message: types.Message, state: FSMContext):
    category_name = message.text
    error_msg = await create_category(message.from_user.id, category_name)
    if error_msg is not None:
        await message.answer(error_msg)
    await state.finish()
    keyboard = await send_category_keyboard(message.from_user.id)
    await bot.send_message(chat_id=message.chat.id, text="Выберите категорию:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == 'Удаление категории')
async def handle_delete_category(message: types.Message, state: FSMContext) -> None:
    """
    Handles the deletion of a category.
    Args:
        message: Message object from the user.
    """
    try:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, selective=True).add(
            *(KeyboardButton(text=label) for label in await get_button_labels(message.from_user.id)))

        await message.answer("Выберите категорию:", reply_markup=keyboard)
        await state.set_state("waiting_for_category_name_for_deletion")
    except Exception as e:
        logging.exception(f"Exception: {e} occurred while handling category deletion.")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delete_task:'))
async def process_callback_delete_task(callback_query: types.CallbackQuery):
    callback_data = callback_query.data.split(':')
    task_id = int(callback_data[1])
    tag = callback_data[2] if len(callback_data) > 2 else None
    if tag == "None":
        tag = None
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"http://127.0.0.1:8000/task/delete_task?task_id={task_id}") as resp:
            pass
    await get_all_tasks(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                        user_id=callback_query.from_user.id, tag=tag
                        )
    await bot.answer_callback_query(callback_query.id, text=f"Task deleted.")


@dp.message_handler(state="waiting_for_task_description")
async def create_task_handler(message: types.Message, state: FSMContext):
    task_description = message.text
    json_data = {
        'title': task_description,
        'user_id': message.from_user.id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8000/task/create', json=json_data) as response:
            r = await response.json()
    await message.answer(f"Таск создан! {task_description}\n\nХотите добавить категорию?",
                         reply_markup=add_category_keyboard)
    await state.update_data(task_id=r['id'], user_id=r['user_id'])
    await state.set_state(CreateTask.waiting_for_add_category)


@dp.callback_query_handler(lambda query: query.data == "add_category:yes", state=CreateTask.waiting_for_add_category)
async def add_category_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = int(data.get('user_id'))
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, selective=True).add(
        *(KeyboardButton(text=label) for label in await get_button_labels(user_id)))

    await query.message.answer("Выберите категорию:", reply_markup=keyboard)
    await query.message.delete()
    await state.set_state(CreateTask.waiting_for_category_selection)


@dp.message_handler(state="waiting_for_category_name_for_deletion")
async def handle_category_name_for_deletion(message: types.Message, state: FSMContext) -> None:
    """
    Handles the category name provided by the user for deletion.
    Args:
        message: Message object from the user.
        state: FSM context to save the state of the conversation.
    """
    try:
        user_id = message.from_user.id
        category_name = message.text

        await delete_category(user_id, category_name)  # Call the function to delete the category
        await message.answer(f"Категория {category_name} удалена.")
        keyboard = await send_category_keyboard(message.from_user.id)
        await bot.send_message(chat_id=message.chat.id, text="Выберете категорию:", reply_markup=keyboard)
        await state.finish()
    except Exception as e:
        logging.exception(f"Exception: {e} occurred while handling category deletion.")


@dp.message_handler(state=CreateTask.waiting_for_category_selection)
async def process_category_name(message: types.Message, state: FSMContext):
    category_name = message.text
    task_data = await state.get_data()
    task_id = task_data['task_id']
    async with aiohttp.ClientSession() as session:
        url = f'http://127.0.0.1:8000/task/add_tag'
        params = {'task_id': task_id, 'tag_name': category_name, 'user_id': message.from_user.id}
        async with session.put(url, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"Error adding category: {resp.status}")
    await message.answer(f"Категория {category_name} добавлена к задаче!")
    await state.finish()
    await bot.send_message(message.chat.id, "Главное меню", reply_markup=main_keyboard)


@dp.callback_query_handler(lambda query: query.data == "add_category:no", state=CreateTask.waiting_for_add_category)
async def no_category_handler(query: types.CallbackQuery, state: FSMContext):
    await query.message.delete()
    await bot.send_message(query.message.chat.id, "Главное меню", reply_markup=main_keyboard)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
