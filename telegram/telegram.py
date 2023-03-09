import logging
from decouple import config

from aiogram import Bot, Dispatcher, executor, types
import re
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = config('API_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def get_all_tasks(chat_id, message_id=None, user_id=None):
    tasks = requests.get(f'http://127.0.0.1:8000/task/get_all_tasks?user_id={user_id}').json()
    buttons = []
    for task in tasks:
        button_text = task.get('title')
        button_callback_data = f"delete_task:{task.get('id')}"
        button = InlineKeyboardButton(text=button_text, callback_data=button_callback_data)
        buttons.append([button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    if not message_id:
        # Send a new message if requested or if no message exists yet
        await bot.send_message(chat_id, 'Ваши задачи', reply_markup=keyboard)
    else:
        # Edit the existing message with the updated inline keyboard
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=keyboard)


@dp.message_handler()
async def show_tasks(message: types.Message):
    tasks_match = re.match(r'^\bТаски\b', message.text, re.IGNORECASE)
    task_match = re.match(r'^\bТаск\b', message.text, re.IGNORECASE)

    if tasks_match:
        await get_all_tasks(message.chat.id, user_id=message.from_user.id)

    elif task_match:
        task_text = re.sub(r'^\s*\bтаск\b\s*', '', message.text, flags=re.IGNORECASE)
        tag_text = re.sub(r'^.*?\bтэг\b\s*', '', task_text, flags=re.IGNORECASE)
        tag_match = requests.get(f'http://127.0.0.1:8000/task/is_exist_tag?tag={tag_text}')
        if tag_match:
            pure_task_text = re.search(r'(?<=\bтаск \b).*?(?=\bтэг\b)', message.text,
                                       re.IGNORECASE | re.UNICODE).group()
        elif not tag_match:
            pure_task_text = task_text

        json_data = {
            'title': pure_task_text,
            'description': '',
            'user_id': message.from_user.id
        }
        r = requests.post('http://127.0.0.1:8000/task/create', json=json_data).json()

        request = requests.put(
            f'http://127.0.0.1:8000/task/add_tag?task_id={r.get("id")}&tag_name={tag_text}') if tag_match.text == 'true' else None
        await message.answer(f"Task '{pure_task_text}' created!")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delete_task:'))
async def process_callback_delete_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split(':')[1])

    r = requests.delete(f'http://127.0.0.1:8000/task/delete_task?task_id={task_id}')

    await get_all_tasks(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                        user_id=callback_query.from_user.id
                        )
    await bot.answer_callback_query(callback_query.id, text=f"Task deleted.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
