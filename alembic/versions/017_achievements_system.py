"""Achievements system — tables and seed.

Revision ID: 017
Revises: 016
Create Date: 2025-01-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED = [
    {"code": "FIRST_STEP", "name_ru": "Первый шаг", "name_en": "First Step", "description_ru": "Создай первую привычку", "description_en": "Create your first habit",
     "unlock_msg_ru": "Отличное начало! Первая привычка создана — ты уже в игре 🚀", "unlock_msg_en": "Great start! Your first habit is created — you're in the game 🚀"},
    {"code": "AWARE_START", "name_ru": "Осознанный старт", "name_en": "Aware Start", "description_ru": "Создай 3 привычки", "description_en": "Create 3 habits",
     "unlock_msg_ru": "Три привычки — фундамент заложен. Продолжай строить систему!", "unlock_msg_en": "Three habits — foundation set. Keep building your system!"},
    {"code": "DAY_ARCHITECT", "name_ru": "Архитектор дня", "name_en": "Day Architect", "description_ru": "Создай 5 привычек", "description_en": "Create 5 habits",
     "unlock_msg_ru": "Ты спроектировал свой день. Теперь действуй как архитектор своей жизни 🏗️", "unlock_msg_en": "You've designed your day. Now act as the architect of your life 🏗️"},
    {"code": "FULL_CONTROL", "name_ru": "Полный контроль", "name_en": "Full Control", "description_ru": "Настрой профиль и напоминания", "description_en": "Complete profile and reminders",
     "unlock_msg_ru": "Система настроена. Дисциплина начинается с порядка ⚙️", "unlock_msg_en": "System configured. Discipline begins with order ⚙️"},
    {"code": "FIRST_MARK", "name_ru": "Первая отметка", "name_en": "First Mark", "description_ru": "Выполни 1 действие", "description_en": "Complete 1 action",
     "unlock_msg_ru": "Есть первая победа! Маленький шаг — большое начало.", "unlock_msg_en": "First victory! Small step — big beginning."},
    {"code": "ACCELERATION", "name_ru": "Ускорение", "name_en": "Acceleration", "description_ru": "Выполни 5 действий", "description_en": "Complete 5 actions",
     "unlock_msg_ru": "Темп набран. Не сбавляй скорость 🔥", "unlock_msg_en": "Momentum gained. Don't slow down 🔥"},
    {"code": "FIRST_10", "name_ru": "Первая десятка", "name_en": "First 10", "description_ru": "Выполни 10 действий", "description_en": "Complete 10 actions",
     "unlock_msg_ru": "10 действий выполнено. Привычка начинает закрепляться.", "unlock_msg_en": "10 actions done. Habit is forming."},
    {"code": "WEEK_FOCUS", "name_ru": "Фокус недели", "name_en": "Week Focus", "description_ru": "Выполни все привычки за день", "description_en": "Complete all habits in one day",
     "unlock_msg_ru": "Идеальный день! Все привычки выполнены.", "unlock_msg_en": "Perfect day! All habits completed."},
    {"code": "PERFECT_MONDAY", "name_ru": "Идеальный понедельник", "name_en": "Perfect Monday", "description_ru": "Выполни все привычки в понедельник", "description_en": "Complete all habits on Monday",
     "unlock_msg_ru": "Понедельник — твой день! Отличное начало недели.", "unlock_msg_en": "Monday is your day! Great start to the week."},
    {"code": "NO_SKIP_3", "name_ru": "Без пропусков 3 дня", "name_en": "No Skip 3", "description_ru": "3 дня подряд без пропусков", "description_en": "3 days in a row with no skips",
     "unlock_msg_ru": "Три дня без пропусков. Сила воли растёт!", "unlock_msg_en": "Three days with no skips. Willpower is growing!"},
    {"code": "STREAK_7", "name_ru": "Серия 7 дней", "name_en": "7 Day Streak", "description_ru": "7 дней подряд с выполнением", "description_en": "7 day streak",
     "unlock_msg_ru": "Неделя подряд! Отличная серия 🔥", "unlock_msg_en": "A full week! Great streak 🔥"},
    {"code": "STREAK_14", "name_ru": "Серия 14 дней", "name_en": "14 Day Streak", "description_ru": "14 дней подряд", "description_en": "14 day streak",
     "unlock_msg_ru": "Две недели! Ты на волне.", "unlock_msg_en": "Two weeks! You're on a roll."},
    {"code": "STREAK_21", "name_ru": "Серия 21 день", "name_en": "21 Day Streak", "description_ru": "21 день подряд", "description_en": "21 day streak",
     "unlock_msg_ru": "21 день — привычка формируется!", "unlock_msg_en": "21 days — habit is forming!"},
    {"code": "STREAK_30", "name_ru": "Серия 30 дней", "name_en": "30 Day Streak", "description_ru": "30 дней подряд", "description_en": "30 day streak",
     "unlock_msg_ru": "Месяц! Ты доказал свою приверженность.", "unlock_msg_en": "A month! You've proven your commitment."},
    {"code": "STREAK_45", "name_ru": "Серия 45 дней", "name_en": "45 Day Streak", "description_ru": "45 дней подряд", "description_en": "45 day streak",
     "unlock_msg_ru": "45 дней без остановки. Ты машина!", "unlock_msg_en": "45 days non-stop. You're a machine!"},
    {"code": "STREAK_60", "name_ru": "Серия 60 дней", "name_en": "60 Day Streak", "description_ru": "60 дней подряд", "description_en": "60 day streak",
     "unlock_msg_ru": "Два месяца! Невероятная серия.", "unlock_msg_en": "Two months! Incredible streak."},
    {"code": "STREAK_90", "name_ru": "Серия 90 дней", "name_en": "90 Day Streak", "description_ru": "90 дней подряд", "description_en": "90 day streak",
     "unlock_msg_ru": "Квартал! Привычка закреплена навсегда.", "unlock_msg_en": "A quarter! Habit is cemented for life."},
    {"code": "STREAK_180", "name_ru": "Серия 180 дней", "name_en": "180 Day Streak", "description_ru": "180 дней подряд", "description_en": "180 day streak",
     "unlock_msg_ru": "Полгода! Ты легенда.", "unlock_msg_en": "Half a year! You're a legend."},
    {"code": "STREAK_365", "name_ru": "Серия 365 дней", "name_en": "365 Day Streak", "description_ru": "365 дней подряд", "description_en": "365 day streak",
     "unlock_msg_ru": "Год! Ты достиг вершины 🏆", "unlock_msg_en": "A year! You've reached the summit 🏆"},
    {"code": "PHOENIX", "name_ru": "Феникс", "name_en": "Phoenix", "description_ru": "Вернись после 5 дней пропусков", "description_en": "Return after 5 days of skips",
     "unlock_msg_ru": "Ты снова в строю! Возрождение сильнее падения.", "unlock_msg_en": "You're back! Rising stronger than the fall."},
    {"code": "PERFECT_DAY", "name_ru": "Идеальный день", "name_en": "Perfect Day", "description_ru": "Первый идеальный день", "description_en": "First perfect day",
     "unlock_msg_ru": "Идеальный день! Каждая привычка выполнена.", "unlock_msg_en": "Perfect day! Every habit completed."},
    {"code": "PERFECT_7", "name_ru": "Идеальная неделя", "name_en": "Perfect 7", "description_ru": "7 идеальных дней подряд", "description_en": "7 perfect days in a row",
     "unlock_msg_ru": "Неделя идеальных дней. Ты неостановим!", "unlock_msg_en": "A week of perfect days. Unstoppable!"},
    {"code": "PERFECT_WEEK", "name_ru": "Идеальная неделя", "name_en": "Perfect Week", "description_ru": "7 идеальных дней подряд", "description_en": "7 consecutive perfect days",
     "unlock_msg_ru": "Полная неделя идеальных дней.", "unlock_msg_en": "Full week of perfect days."},
    {"code": "PERFECT_14", "name_ru": "14 идеальных дней", "name_en": "14 Perfect Days", "description_ru": "14 идеальных дней", "description_en": "14 perfect days",
     "unlock_msg_ru": "Две недели идеала. Впечатляюще!", "unlock_msg_en": "Two weeks of perfection. Impressive!"},
    {"code": "PERFECT_MONTH", "name_ru": "Идеальный месяц", "name_en": "Perfect Month", "description_ru": "30 идеальных дней", "description_en": "30 perfect days",
     "unlock_msg_ru": "Месяц без единого пропуска. Легендарно.", "unlock_msg_en": "A month without a single skip. Legendary."},
    {"code": "ABSOLUTE", "name_ru": "Абсолют", "name_en": "Absolute", "description_ru": "3 идеальные недели в месяце", "description_en": "3 perfect weeks in a month",
     "unlock_msg_ru": "Три идеальные недели. Ты на другом уровне.", "unlock_msg_en": "Three perfect weeks. You're on another level."},
    {"code": "MAXIMALIST", "name_ru": "Максималист", "name_en": "Maximalist", "description_ru": "10 идеальных дней подряд", "description_en": "10 perfect days streak",
     "unlock_msg_ru": "10 идеальных дней подряд. Максимум!", "unlock_msg_en": "10 perfect days in a row. Maximum!"},
    {"code": "MARK_50", "name_ru": "50 отметок", "name_en": "50 Marks", "description_ru": "50 выполненных действий", "description_en": "50 completed actions",
     "unlock_msg_ru": "50 действий! Привычка — часть тебя.", "unlock_msg_en": "50 actions! Habit is part of you."},
    {"code": "MARK_100", "name_ru": "100 отметок", "name_en": "100 Marks", "description_ru": "100 выполненных действий", "description_en": "100 completed actions",
     "unlock_msg_ru": "Сотня! Ты прошёл путь.", "unlock_msg_en": "A hundred! You've come far."},
    {"code": "MARK_250", "name_ru": "250 отметок", "name_en": "250 Marks", "description_ru": "250 выполненных действий", "description_en": "250 completed actions",
     "unlock_msg_ru": "250 действий. Результат налицо.", "unlock_msg_en": "250 actions. Results speak."},
    {"code": "MARK_500", "name_ru": "500 отметок", "name_en": "500 Marks", "description_ru": "500 выполненных действий", "description_en": "500 completed actions",
     "unlock_msg_ru": "500! Ты — эталон дисциплины.", "unlock_msg_en": "500! You're the epitome of discipline."},
    {"code": "MARK_1000", "name_ru": "1000 отметок", "name_en": "1000 Marks", "description_ru": "1000 выполненных действий", "description_en": "1000 completed actions",
     "unlock_msg_ru": "Тысяча! Ты вошёл в историю 🏆", "unlock_msg_en": "A thousand! You've made history 🏆"},
    {"code": "SUPERACTIVE", "name_ru": "Суперактивный", "name_en": "Superactive", "description_ru": "20 действий за день", "description_en": "20 actions in one day",
     "unlock_msg_ru": "20 действий за день! Взрыв продуктивности.", "unlock_msg_en": "20 actions in a day! Productivity explosion."},
    {"code": "STRONG_WEEK", "name_ru": "Сильная неделя", "name_en": "Strong Week", "description_ru": "70 действий за неделю", "description_en": "70 actions in 7 days",
     "unlock_msg_ru": "70 действий за неделю. Мощный темп!", "unlock_msg_en": "70 actions in a week. Powerful pace!"},
    {"code": "PRODUCTIVE_MONTH", "name_ru": "Продуктивный месяц", "name_en": "Productive Month", "description_ru": "300 действий за месяц", "description_en": "300 actions in a month",
     "unlock_msg_ru": "300 за месяц. Ты машина продуктивности.", "unlock_msg_en": "300 in a month. You're a productivity machine."},
    {"code": "FLEXIBLE", "name_ru": "Гибкий", "name_en": "Flexible", "description_ru": "Измени привычку и сохрани серию", "description_en": "Change habit and preserve streak",
     "unlock_msg_ru": "Гибкость и последовательность — твой козырь.", "unlock_msg_en": "Flexibility and consistency — your ace."},
    {"code": "GROWTH", "name_ru": "Рост", "name_en": "Growth", "description_ru": "Увеличь цель привычки", "description_en": "Increase habit goal",
     "unlock_msg_ru": "Цель растёт — растёшь и ты.", "unlock_msg_en": "Goal grows — so do you."},
    {"code": "MULTIFOCUS", "name_ru": "Мультифокус", "name_en": "Multifocus", "description_ru": "5 привычек ежедневно 14 дней", "description_en": "5 habits daily for 14 days",
     "unlock_msg_ru": "Пять привычек две недели. Мультитаскинг мастер.", "unlock_msg_en": "Five habits for two weeks. Multitasking master."},
    {"code": "BALANCE", "name_ru": "Баланс", "name_en": "Balance", "description_ru": "3 категории активны 30 дней", "description_en": "3 categories active 30 days",
     "unlock_msg_ru": "Баланс во всём. Гармония достигнута.", "unlock_msg_en": "Balance in all. Harmony achieved."},
    {"code": "EXPERIMENTER", "name_ru": "Экспериментатор", "name_en": "Experimenter", "description_ru": "Новая привычка активна 7 дней", "description_en": "New habit active 7 days",
     "unlock_msg_ru": "Неделя с новой привычкой. Эксперимент удался!", "unlock_msg_en": "A week with a new habit. Experiment succeeded!"},
    {"code": "FIRST_FRIEND", "name_ru": "Первый друг", "name_en": "First Friend", "description_ru": "Пригласи 1 друга", "description_en": "Invite 1 friend",
     "unlock_msg_ru": "Первый друг в команде! Вместе веселее.", "unlock_msg_en": "First friend on the team! More fun together."},
    {"code": "TEAM_START", "name_ru": "Старт команды", "name_en": "Team Start", "description_ru": "Пригласи 3 друзей", "description_en": "Invite 3 friends",
     "unlock_msg_ru": "Три друга! Команда растёт.", "unlock_msg_en": "Three friends! Team is growing."},
    {"code": "AMBASSADOR", "name_ru": "Посол", "name_en": "Ambassador", "description_ru": "Пригласи 10 друзей", "description_en": "Invite 10 friends",
     "unlock_msg_ru": "10 друзей! Ты — посол продуктивности.", "unlock_msg_en": "10 friends! You're an ambassador of productivity."},
    {"code": "SUPPORTER_1M", "name_ru": "Поддержка 1 мес", "name_en": "1 Month Supporter", "description_ru": "Подписка от 1 месяца", "description_en": "Subscription 1+ month",
     "unlock_msg_ru": "Месяц поддержки. Спасибо, что с нами!", "unlock_msg_en": "A month of support. Thanks for being with us!"},
    {"code": "CHOICE_3M", "name_ru": "Выбор 3 мес", "name_en": "3 Month Choice", "description_ru": "Подписка от 3 месяцев", "description_en": "Subscription 3+ months",
     "unlock_msg_ru": "Три месяца — осознанный выбор. Респект!", "unlock_msg_en": "Three months — a conscious choice. Respect!"},
    {"code": "PLAN_6M", "name_ru": "План 6 мес", "name_en": "6 Month Plan", "description_ru": "Подписка от 6 месяцев", "description_en": "Subscription 6+ months",
     "unlock_msg_ru": "Полгода с нами. Ты наш!", "unlock_msg_en": "Half a year with us. You're ours!"},
    {"code": "INVESTOR_12M", "name_ru": "Инвестор года", "name_en": "Year Investor", "description_ru": "Подписка от 12 месяцев", "description_en": "Subscription 12+ months",
     "unlock_msg_ru": "Год поддержки! Ты — инвестор в себя 🏆", "unlock_msg_en": "A year of support! You're investing in yourself 🏆"},
    {"code": "TEAM_DISCIPLINE", "name_ru": "Дисциплина команды", "name_en": "Team Discipline", "description_ru": "3 друга с серией 7+ дней", "description_en": "3 referrals with 7+ day streak",
     "unlock_msg_ru": "Команда дисциплинирована. Лидерство в действии.", "unlock_msg_en": "Team is disciplined. Leadership in action."},
    {"code": "SOCIAL_DRIVE", "name_ru": "Социальный драйв", "name_en": "Social Drive", "description_ru": "14 дней синхронно с другом", "description_en": "14 days synced with friend",
     "unlock_msg_ru": "Две недели в ритме с другом. Синхронность!", "unlock_msg_en": "Two weeks in sync with a friend. Synchronicity!"},
    {"code": "LEADER", "name_ru": "Лидер", "name_en": "Leader", "description_ru": "5 приглашённых активны 30 дней", "description_en": "5 referrals active 30 days",
     "unlock_msg_ru": "Пять активных друзей месяц. Ты — лидер!", "unlock_msg_en": "Five active friends for a month. You're a leader!"},
]


def upgrade() -> None:
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name_ru", sa.Text(), nullable=False),
        sa.Column("name_en", sa.Text(), nullable=False),
        sa.Column("description_ru", sa.Text(), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("unlock_msg_ru", sa.Text(), nullable=False),
        sa.Column("unlock_msg_en", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_achievements_code"),
    )
    op.create_index("ix_achievements_code", "achievements", ["code"], unique=True)

    op.create_table(
        "user_achievements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["achievement_id"], ["achievements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )
    op.create_index("idx_user_achievements_user_id", "user_achievements", ["user_id"], unique=False)

    # Seed achievements
    ach = sa.table(
        "achievements",
        sa.column("code", sa.String),
        sa.column("name_ru", sa.Text),
        sa.column("name_en", sa.Text),
        sa.column("description_ru", sa.Text),
        sa.column("description_en", sa.Text),
        sa.column("unlock_msg_ru", sa.Text),
        sa.column("unlock_msg_en", sa.Text),
    )
    op.bulk_insert(ach, SEED)


def downgrade() -> None:
    op.drop_index("idx_user_achievements_user_id", table_name="user_achievements")
    op.drop_table("user_achievements")
    op.drop_index("ix_achievements_code", table_name="achievements")
    op.drop_table("achievements")
