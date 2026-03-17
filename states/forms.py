from aiogram.fsm.state import State, StatesGroup

class StoryInput(StatesGroup):

    choosing_content_type = State()
    choosing_model = State()
    waiting_for_text = State()
    