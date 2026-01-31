"""
FSM state groups for all user scenarios.
"""

from aiogram.fsm.state import State, StatesGroup


class SettingsFSM(StatesGroup):
    """Settings flow."""

    waiting_timezone = State()
    waiting_notification_time = State()


class HabitFSM(StatesGroup):
    """Create habit flow."""

    waiting_name = State()
    waiting_description = State()
    waiting_schedule_type = State()
    waiting_schedule_time = State()
    waiting_schedule_days = State()
    waiting_confirm = State()


class HabitEditFSM(StatesGroup):
    """Edit habit flow."""

    selecting_habit = State()
    selecting_field = State()
    waiting_new_value = State()


class HabitLogFSM(StatesGroup):
    """Log habit (complete/decline) flow."""

    selecting_habit = State()
    adding_decline_note = State()


class PaymentFSM(StatesGroup):
    """Payment flow."""

    selecting_amount = State()
    selecting_method = State()
    processing = State()


class AdminFSM(StatesGroup):
    """Admin panel flow."""

    main_menu = State()
    viewing_metrics = State()
    viewing_logs = State()
    broadcasting = State()
