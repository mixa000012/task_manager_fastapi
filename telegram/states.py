from aiogram.dispatcher.filters.state import State, StatesGroup
class CreateTask(StatesGroup):
    waiting_for_task_description = State()
    waiting_for_add_category = State()
    waiting_for_category_name = State()
    waiting_for_category_selection = State()


class CreateCategory(StatesGroup):
    name = State()

