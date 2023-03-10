from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
from decouple import config
from aiogram.dispatcher import FSMContext

from aiogram import Bot, Dispatcher, executor, types
import re
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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


class CreateTask(StatesGroup):
    waiting_for_task_description = State()
    waiting_for_add_category = State()
    waiting_for_category_name = State()
    waiting_for_category_selection = State()


class CreateCategory(StatesGroup):
    name = State()


def get_buttons(user_id: int):
    button_labels = requests.get(f'http://127.0.0.1:8000/task/get_all_tags?user_id={user_id}').json()
    return button_labels


async def handle_category_click(message: types.Message):
    button_label = message.text
    tasks = requests.get(
        f'http://127.0.0.1:8000/task/get_tasks_by_tag?user_id={message.from_user.id}&tag={button_label}').json()
    buttons = []
    for task in tasks:
        button_text = task.get('title')
        button_callback_data = f"delete_task:{task.get('id')}"
        button = InlineKeyboardButton(text=button_text, callback_data=button_callback_data)
        buttons.append([button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(message.chat.id, 'Ваши задачи', reply_markup=keyboard)


@dp.message_handler(lambda message: message.text in get_buttons(message.from_user.id))
async def handle_category_click_wrapper(message: types.Message):
    await handle_category_click(message)


async def get_all_tasks(chat_id, message_id=None, user_id=None, chat_type=None):
    tasks = requests.get(f'http://127.0.0.1:8000/task/get_all_tasks?user_id={user_id}').json()
    buttons = []
    for task in tasks:
        button_text = task.get('title')
        button_callback_data = f"delete_task:{task.get('id')}"
        button = InlineKeyboardButton(text=button_text, callback_data=button_callback_data)
        buttons.append([button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    if chat_type == 'private':
        # Send a new message if requested or if no message exists yet
        await bot.send_message(chat_id, 'Ваши задачи', reply_markup=keyboard)
    else:
        # Edit the existing message with the updated inline keyboard
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text in ['Создать таск', 'Категории', 'Все задачи'])
async def main_menu_handler(message: types.Message, state: FSMContext):
    if message.text == 'Создать таск':
        await message.answer("Введите описание таска:")

        await state.set_state("waiting_for_task_description")

    elif message.text == 'Категории':
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, selective=True).add(
            *(KeyboardButton(text=label) for label in get_buttons(message.from_user.id)))
        new_category_button = KeyboardButton(text='Создать новую категорию')

        keyboard.add(new_category_button)

        keyboard.add(KeyboardButton(text='Home'))
        await bot.send_message(chat_id=message.chat.id, text="Select a category:", reply_markup=keyboard)
    elif message.text == 'Все задачи':
        await get_all_tasks(chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id,
                            chat_type=message.chat.type)


@dp.message_handler(lambda message: message.text == 'Создать новую категорию', state=None)
async def create_category_handler(message: types.Message):
    await message.answer('Введите название новой категории:')
    await CreateCategory.name.set()


@dp.message_handler(state=CreateCategory.name)
async def process_category_name(message: types.Message, state: FSMContext):
    # Create the new category in the database
    category_name = message.text
    json_data = {
        'tag': category_name,
    }
    r = requests.post(f'http://127.0.0.1:8000/task/create_tag?user_id={message.from_user.id}', json=json_data).text

    # Return to the list of categories
    await message.answer(f'Категория "{category_name}" создана')
    await state.finish()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, selective=True).add(
        *(KeyboardButton(text=label) for label in get_buttons(message.from_user.id)))
    new_category_button = KeyboardButton(text='Создать новую категорию')

    keyboard.add(new_category_button)

    keyboard.add(KeyboardButton(text='Home'))
    await bot.send_message(chat_id=message.chat.id, text="Select a category:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delete_task:'))
async def process_callback_delete_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split(':')[1])

    r = requests.delete(f'http://127.0.0.1:8000/task/delete_task?task_id={task_id}')

    await get_all_tasks(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                        user_id=callback_query.from_user.id
                        )
    await bot.answer_callback_query(callback_query.id, text=f"Task deleted.")


# Handler for the "Home" button in the categories and tasks menus
@dp.message_handler(lambda message: message.text == 'Home')
async def home_button_handler(message: types.Message):
    await message.answer("Главное меню", reply_markup=main_keyboard)


@dp.message_handler(state="waiting_for_task_description")
async def create_task_handler(message: types.Message, state: FSMContext):
    task_description = message.text
    json_data = {
        'title': task_description,
        'user_id': message.from_user.id
    }
    r = requests.post('http://127.0.0.1:8000/task/create', json=json_data).json()
    await message.answer(f"Таск создан! {task_description}\n\nХотите добавить категорию?",
                         reply_markup=add_category_keyboard)
    await state.update_data(task_id=r['id'],user_id=r['user_id'])
    await state.set_state(CreateTask.waiting_for_add_category)


@dp.callback_query_handler(lambda query: query.data == "add_category:yes", state=CreateTask.waiting_for_add_category)
async def add_category_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = int(data.get('user_id'))
    tasks = requests.get(f'http://127.0.0.1:8000/task/get_all_tasks?user_id={user_id}').json()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4, selective=True).add(
        *(KeyboardButton(text=label) for label in get_buttons(user_id)))

    await query.message.answer("Выберите категорию:", reply_markup=keyboard)
    await state.set_state(CreateTask.waiting_for_category_selection)

@dp.message_handler(state=CreateTask.waiting_for_category_selection)
async def process_category_name(message: types.Message, state: FSMContext):
    category_name = message.text
    task_data = await state.get_data()
    task_id = task_data['task_id']
    request = requests.put(
        f'http://127.0.0.1:8000/task/add_tag?task_id={task_id}&tag_name={category_name}&user_id={message.from_user.id}')
    await message.answer(f"Категория {category_name} добавлена к задаче!")
    await state.finish()
    await bot.send_message(message.chat.id, "Главное меню", reply_markup=main_keyboard)



@dp.callback_query_handler(lambda query: query.data == "add_category:no", state=CreateTask.waiting_for_add_category)
async def no_category_handler(query: types.CallbackQuery, state: FSMContext):
    await query.message.delete()
    await bot.send_message(query.message.chat.id, "Главное меню", reply_markup=main_keyboard)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
