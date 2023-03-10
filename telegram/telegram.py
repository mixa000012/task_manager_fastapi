import logging
from decouple import config

from aiogram import Bot, Dispatcher, executor, types
import re
import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = config('API_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def get_button_lanels(user_id):
    button_labels = requests.get(f'http://127.0.0.1:8000/task/get_all_tags?user_id={user_id}').json()
    button_labels += ['Создать категорию']
    return button_labels


async def on_button_click(message: types.Message):
    button_label = message.text
    text = requests.get(
        f'http://127.0.0.1:8000/task/get_tasks_by_tag?user_id={message.from_user.id}&tag={button_label}').json()
    if text:
        task_list = ''
        for task in text:
            task_list += task + "\n"
    else:
        task_list ='У вас нет задач в этой категории!'

    await bot.send_message(chat_id=message.from_user.id, text=task_list)
    await start_handler(message)

@dp.message_handler(commands=['categories'])
async def start_handler(message: types.Message):
    button_labels = get_button_lanels(message.from_user.id)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, selective=True).add(
        *(KeyboardButton(text=label) for label in button_labels))

    await bot.send_message(chat_id=message.chat.id, text="Choose a button:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text in get_button_lanels(message.from_user.id))
async def button_click_handler(message: types.Message):
    await on_button_click(message)


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
    tag_match = re.match(r'^тэг\s*(.*)', message.text, re.IGNORECASE)

    if tasks_match:
        await get_all_tasks(message.chat.id, user_id=message.from_user.id)

    elif task_match:
        task_text = re.sub(r'^\s*\bтаск\b\s*', '', message.text, flags=re.IGNORECASE)
        tag_text = re.sub(r'^.*?\bтэг\b\s*', '', task_text, flags=re.IGNORECASE)
        tag_match = requests.get(f'http://127.0.0.1:8000/task/is_exist_tag?tag={tag_text}')
        if tag_match.text == 'true':
            pure_task_text = re.search(r'(?<=\bтаск \b).*?(?=\bтэг\b)', message.text,
                                       re.IGNORECASE | re.UNICODE).group()

        elif tag_match.text == 'false' or not tag_match:
            pure_task_text = task_text

        json_data = {
            'title': pure_task_text,
            'user_id': message.from_user.id
        }
        r = requests.post('http://127.0.0.1:8000/task/create', json=json_data).json()
        request = requests.put(
            f'http://127.0.0.1:8000/task/add_tag?task_id={r.get("id")}&tag_name={tag_text}') if tag_match.text == 'true' else None
        await message.answer(f"Task '{pure_task_text}' created!")

    elif tag_match:
        tag_text = tag_match.group(1)

        json_data = {
            'tag': tag_text.strip(),
        }

        r = requests.post(f'http://127.0.0.1:8000/task/create_tag?user_id={message.from_user.id}', json=json_data).text
        await message.answer(f"Tag '{tag_text.strip()}' created!{r}")


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
