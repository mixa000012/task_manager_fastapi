import logging

from aiogram import Bot, Dispatcher, executor, types
import re
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = ''

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
    tag_match = re.search(r'\bтэг\s*:\s*(\S+)\b', message.text, re.IGNORECASE)
    if re.match(r'^\bТаски\b', message.text, re.IGNORECASE):
        await get_all_tasks(message.chat.id, user_id=message.from_user.id)

        if tag_match:
            tag = tag_match.group(1)
            await bot.send_message(chat_id=message.chat.id,
                                   text=f'Got it! You want to do a task with the tag "{tag}". 🤖👍')
    elif re.match(r'^\bТаск\b', message.text, re.IGNORECASE):
        task_text = message.text.replace('Таск', '').strip()
        json_data = {
            'title': task_text,
            'description': '',
            'user_id': message.from_user.id
        }
        r = requests.post('http://127.0.0.1:8000/task/create', json=json_data)
        await message.answer(f"Task '{task_text}' created!")


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
