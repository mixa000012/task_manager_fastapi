# -*- coding: utf-8 -*-
import asyncio
import logging

import aiohttp
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import executor
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton
from aiogram.types import ReplyKeyboardMarkup
from decouple import config
from keyboards import add_category_keyboard
from keyboards import main_keyboard
from states import CreateCategory
from states import CreateTask
from utils import create_category
from utils import delete_category
from utils import get_all_tasks
from utils import get_button_labels
from utils import send_category_keyboard

API_TOKEN = config("API_TOKEN")
task_url = config("API_ROUT")
storage = MemoryStorage()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Я помогу тебе управлять своими задачами. Нажми на кнопку, чтобы начать",
        reply_markup=main_keyboard,
    )


@dp.message_handler(
    lambda message: message.text in ["Создать таск", "Категории", "Все задачи"]
)
async def main_menu_handler(message: types.Message, state: FSMContext):
    if message.text == "Создать таск":
        await message.answer("Введите описание таска:")
        await state.set_state("waiting_for_task_description")

    elif message.text == "Категории":
        keyboard = await send_category_keyboard(message.from_user.id)
        await bot.send_message(
            chat_id=message.chat.id, text="Выберете категорию:", reply_markup=keyboard
        )

    elif message.text == "Все задачи":
        await get_all_tasks(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            message_id=message.message_id,
            chat_type=message.chat.type,
            bot=bot,
        )


@dp.message_handler(lambda message: message.text == "Home")
async def home_button_handler(message: types.Message):
    await message.answer("Главное меню", reply_markup=main_keyboard)


async def is_in_buttons(user_id: int, text: str):
    async with aiohttp.ClientSession() as session:
        url = f"{task_url}/get_all_tags"
        params = {"user_id": user_id}
        async with session.get(url, params=params) as resp:
            button_labels = await resp.json()
    return text in button_labels


async def handle_category_click(message: types.Message):
    tag = message.text
    await get_all_tasks(
        chat_id=message.chat.id,
        message_id=message.message_id,
        user_id=message.from_user.id,
        tag=tag,
        chat_type=message.chat.type,
        bot=bot,
    )


@dp.message_handler(
    lambda message: message.text == "Создать новую категорию", state=None
)
async def create_category_handler(message: types.Message):
    await message.answer("Введите название новой категории:")
    await CreateCategory.name.set()


# todo не пускать пустые задачи
@dp.message_handler(state=CreateCategory.name)
async def process_create_category(message: types.Message, state: FSMContext):
    if message.text == "Home":
        await bot.send_message(
            message.chat.id, "Главное меню", reply_markup=main_keyboard
        )
    else:
        category_name = message.text
        error_msg = await create_category(message.from_user.id, category_name)
        if error_msg is not None:
            await message.answer(error_msg)
        else:
            await state.finish()
        keyboard = await send_category_keyboard(message.from_user.id)
        await bot.send_message(
            chat_id=message.chat.id, text="Выберите категорию:", reply_markup=keyboard
        )


@dp.message_handler(lambda message: message.text == "Удаление категории")
async def handle_delete_category(message: types.Message, state: FSMContext) -> None:
    """
    Handles the deletion of a category.
    Args:
        message: Message object from the user.
    """
    get_len = await get_button_labels(message.from_user.id)

    try:
        if len(get_len) > 0:
            keyboard = ReplyKeyboardMarkup(
                resize_keyboard=True, row_width=4, selective=True
            ).add(
                *(
                    KeyboardButton(text=label)
                    for label in await get_button_labels(message.from_user.id)
                )
            )

            await message.answer("Выберите категорию:", reply_markup=keyboard)
            await state.set_state("waiting_for_category_name_for_deletion")
        else:
            await message.answer("Вам нечего удалять!")
    except Exception as e:
        logging.exception(f"Exception: {e} occurred while handling category deletion.")


@dp.message_handler(
    lambda message: asyncio.ensure_future(
        is_in_buttons(message.from_user.id, message.text)
    )
)
async def handle_category_click_wrapper(message: types.Message):
    await handle_category_click(message)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("delete_task:"))
async def process_callback_delete_task(callback_query: types.CallbackQuery):
    callback_data = callback_query.data.split(":")
    task_id = int(callback_data[1])
    tag = callback_data[2] if len(callback_data) > 2 else None
    if tag == "None":
        tag = None
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{task_url}/delete_task?task_id={task_id}"):
            pass
    await get_all_tasks(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        user_id=callback_query.from_user.id,
        tag=tag,
        bot=bot,
    )
    await bot.answer_callback_query(callback_query.id, text="Task deleted.")


@dp.message_handler(state="waiting_for_task_description")
async def create_task_handler(message: types.Message, state: FSMContext):
    task_description = message.text
    if task_description not in ["Все задачи", "Категории", "Создать таск"]:
        json_data = {"title": task_description, "user_id": message.from_user.id}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{task_url}/create", json=json_data) as response:
                r = await response.json()
        await message.answer(
            f"Таск создан! {task_description}\n\nХотите добавить категорию?",
            reply_markup=add_category_keyboard,
        )
        await state.update_data(task_id=r["id"], user_id=r["user_id"])
        await state.set_state(CreateTask.waiting_for_add_category)
    else:
        await message.answer("Недопустимая название таска!")


@dp.callback_query_handler(
    lambda query: query.data == "add_category:yes",
    state=CreateTask.waiting_for_add_category,
)
async def add_category_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = int(data.get("user_id"))
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=4, selective=True
    ).add(*(KeyboardButton(text=label) for label in await get_button_labels(user_id)))

    await query.message.answer("Выберите категорию:", reply_markup=keyboard)
    await query.message.delete()
    await state.set_state(CreateTask.waiting_for_category_selection)


# todo проверка на то, что удалялись существубщие категории, проверка при создании на кнопки, чтоб они не создавались


@dp.message_handler(state="waiting_for_category_name_for_deletion")
async def handle_category_name_for_deletion(
    message: types.Message, state: FSMContext
) -> None:
    """
    Handles the category name provided by the user for deletion.
    Args:
        message: Message object from the user.
        state: FSM context to save the state of the conversation.
    """
    try:
        user_id = message.from_user.id
        category_name = message.text
        if category_name in await get_button_labels(user_id):

            await delete_category(
                user_id, category_name
            )  # Call the function to delete the category
            await message.answer(f"Категория {category_name} удалена.")
            keyboard = await send_category_keyboard(message.from_user.id)
            await bot.send_message(
                chat_id=message.chat.id,
                text="Выберете категорию:",
                reply_markup=keyboard,
            )
            await state.finish()
        else:
            await message.answer("Такой категории не существует!")
    except Exception as e:
        logging.exception(f"Exception: {e} occurred while handling category deletion.")


@dp.message_handler(state=CreateTask.waiting_for_category_selection)
async def process_category_name(message: types.Message, state: FSMContext):
    category_name = message.text
    task_data = await state.get_data()
    task_id = task_data["task_id"]
    async with aiohttp.ClientSession() as session:
        url = f"{task_url}/add_tag"
        params = {
            "task_id": task_id,
            "tag_name": category_name,
            "user_id": message.from_user.id,
        }
        async with session.put(url, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"Error adding category: {resp.status}")
    await message.answer(f"Категория {category_name} добавлена к задаче!")
    await state.finish()
    await bot.send_message(message.chat.id, "Главное меню", reply_markup=main_keyboard)


@dp.callback_query_handler(
    lambda query: query.data == "add_category:no",
    state=CreateTask.waiting_for_add_category,
)
async def no_category_handler(query: types.CallbackQuery, state: FSMContext):
    await query.message.delete()
    await state.finish()
    await bot.send_message(
        query.message.chat.id, "Главное меню", reply_markup=main_keyboard
    )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
