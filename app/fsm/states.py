"""FSM states for habit creation."""

from aiogram.fsm.state import State, StatesGroup


class AddHabitStates(StatesGroup):
    presets = State()
    weekdays = State()
    times = State()
