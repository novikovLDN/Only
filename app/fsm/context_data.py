"""
Ключи FSM context data.

Единая точка для ключей — избегаем опечаток и magic strings.
"""

# HabitCreateFSM
FSM_HABIT_TEMPLATE_ID = "template_id"
FSM_HABIT_NAME = "name"
FSM_HABIT_EMOJI = "emoji"  # optional
FSM_HABIT_DAYS = "days"  # list[int] 0-6
FSM_HABIT_TIMES = "times"  # list[str] "09:00", ...
FSM_HABIT_CREATED_AT = "habit_created_at"  # для timeout

# HabitDeclineFSM
FSM_DECLINE_HABIT_ID = "habit_id"

# SubscriptionFSM
FSM_SUB_PLAN_ID = "plan_id"
FSM_SUB_AMOUNT = "amount"
FSM_SUB_PROVIDER = "provider"

# BalanceFSM
FSM_BALANCE_AMOUNT = "amount"
FSM_BALANCE_PROVIDER = "provider"
