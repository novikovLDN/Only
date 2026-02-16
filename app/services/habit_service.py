"""Habit service."""

from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Habit, HabitTime


def _parse_time(s: str) -> time:
    try:
        return datetime.strptime(s, "%H:%M").time()
    except (ValueError, TypeError):
        parts = str(s).split(":")
        h = int(parts[0]) if parts else 0
        m = int(parts[1]) if len(parts) > 1 else 0
        return time(h % 24, m % 60)


PRESETS = [
    "🏃 Бег",
    "📚 Чтение",
    "💧 Пить воду",
    "🧘 Медитация",
    "💪 Тренировка",
    "🌅 Ранний подъём",
    "📝 Ведение дневника",
    "🥗 Правильное питание",
    "📖 Изучение языка",
    "🧠 Развитие навыков",
    "📵 Меньше соцсетей",
    "🛏 Режим сна",
    "🚶 Прогулка",
    "💼 Фокус на работе",
    "🧹 Порядок дома",
    "🙏 Благодарность",
    "🎯 Работа над целью",
    "🎵 Практика музыки",
    "💰 Контроль бюджета",
    "📦 Планирование дня",
]

FREE_PRESET_LIMIT = 3


async def create(
    session: AsyncSession,
    user_id: int,
    title: str,
    weekdays: list[int],
    times: list[str],
) -> Habit:
    habit = Habit(user_id=user_id, title=title, is_active=True)
    session.add(habit)
    await session.flush()
    for wd in weekdays:
        for t in times:
            ht = HabitTime(habit_id=habit.id, weekday=wd, time=_parse_time(t))
            session.add(ht)
    await session.flush()
    await session.refresh(habit)
    return habit


async def get_user_habits(session: AsyncSession, user_id: int) -> list[Habit]:
    result = await session.execute(
        select(Habit).where(Habit.user_id == user_id, Habit.is_active == True).order_by(Habit.created_at)
    )
    return list(result.scalars().unique().all())


async def get_by_id(session: AsyncSession, habit_id: int) -> Habit | None:
    result = await session.execute(select(Habit).where(Habit.id == habit_id))
    return result.scalar_one_or_none()


async def get_habit_times(session: AsyncSession, habit_id: int) -> list[tuple[int, str]]:
    result = await session.execute(
        select(HabitTime.weekday, HabitTime.time).where(HabitTime.habit_id == habit_id)
    )
    return [(row[0], row[1].strftime("%H:%M") if hasattr(row[1], "strftime") else str(row[1])) for row in result.all()]


async def update_habit_times(
    session: AsyncSession,
    habit_id: int,
    weekdays: list[int],
    times: list[str],
) -> None:
    from sqlalchemy import delete
    await session.execute(delete(HabitTime).where(HabitTime.habit_id == habit_id))
    for wd in weekdays:
        for t in times:
            ht = HabitTime(habit_id=habit_id, weekday=wd, time=_parse_time(t))
            session.add(ht)
    await session.flush()


async def delete_habit(session: AsyncSession, habit: Habit) -> None:
    await session.delete(habit)
    await session.flush()


async def count_user_habits(session: AsyncSession, user_id: int) -> int:
    from sqlalchemy import func
    result = await session.execute(
        select(func.count()).select_from(Habit).where(Habit.user_id == user_id, Habit.is_active == True)
    )
    return result.scalar() or 0
