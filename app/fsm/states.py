"""
FSM state groups для всех пошаговых сценариев.

Каждый state — один шаг диалога. Переходы через handlers.
Бизнес-логика в domain services, FSM только управляет flow.
"""

from aiogram.fsm.state import State, StatesGroup


class HabitCreateFSM(StatesGroup):
    """Создание привычки: шаблон/своя → дни → время → подтверждение."""

    # Шаг 1: шаблон (быстрый старт) или своя привычка
    choosing_template = State()
    # Шаг 2: ввод названия (только для «своя»)
    waiting_name = State()
    # Шаг 3: multi-select дней недели (0=Пн .. 6=Вс)
    choosing_days = State()
    # Шаг 4: multi-select времени (слоты: 06:00, 09:00, 12:00, ...)
    choosing_time = State()
    # Шаг 5: подтверждение
    confirming = State()


class HabitDeclineFSM(StatesGroup):
    """Отклонение привычки с комментарием."""

    # habit_id уже в data от callback
    adding_note = State()


class SubscriptionFSM(StatesGroup):
    """Покупка подписки."""

    choosing_plan = State()
    choosing_payment = State()
    processing = State()


class BalanceFSM(StatesGroup):
    """Пополнение баланса."""

    choosing_amount = State()
    choosing_provider = State()
    processing = State()


class SettingsFSM(StatesGroup):
    """Настройки."""

    waiting_timezone = State()
    waiting_notification_time = State()


class HabitEditFSM(StatesGroup):
    """Редактирование привычки."""

    selecting_habit = State()
    selecting_field = State()
    waiting_new_value = State()


class AdminFSM(StatesGroup):
    """Админ-панель."""

    main_menu = State()
    viewing_metrics = State()
    viewing_logs = State()
    broadcasting = State()


# Alias для обратной совместимости
HabitFSM = HabitCreateFSM
HabitLogFSM = HabitDeclineFSM
PaymentFSM = BalanceFSM
