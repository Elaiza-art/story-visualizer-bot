# states/forms.py
from aiogram.fsm.state import State, StatesGroup

class StoryInput(StatesGroup):
    waiting_for_text = State() # состояние: ввод текста истории
    