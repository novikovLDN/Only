"""FSM states."""

from aiogram.fsm.state import State, StatesGroup


class AddHabitStates(StatesGroup):
    presets = State()
    custom_text = State()
    weekdays = State()
    times = State()
