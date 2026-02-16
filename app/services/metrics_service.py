"""User metrics — computation and persistence for achievements."""

import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Habit, HabitLog, HabitTime, Referral, User, UserMetrics

logger = logging.getLogger(__name__)


def _user_today(user: User) -> date:
    tz_name = user.timezone or "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    return datetime.now(tz).date()


def _user_now(user: User) -> datetime:
    tz_name = user.timezone or "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    return datetime.now(tz)


async def get_or_create_metrics(session: AsyncSession, user_id: int) -> UserMetrics:
    m = await session.get(UserMetrics, user_id)
    if m is None:
        m = UserMetrics(user_id=user_id)
        session.add(m)
        await session.flush()
    return m


async def recalculate_user_metrics(
    session: AsyncSession,
    user_id: int,
    user: User | None = None,
) -> UserMetrics:
    """Full recalculation from habit_logs, habits, referrals. Uses user timezone if provided."""
    if user is None:
        user = await session.get(User, user_id)
    m = await get_or_create_metrics(session, user_id)
    today = _user_today(user) if user else date.today()
    tz_name = (user.timezone or "UTC") if user else "UTC"

    # Total completions
    r = await session.execute(
        select(func.count()).select_from(HabitLog).where(
            HabitLog.user_id == user_id, HabitLog.status == "done"
        )
    )
    m.total_completions = r.scalar() or 0

    # Habits count
    r = await session.execute(
        select(func.count()).select_from(Habit).where(
            Habit.user_id == user_id, Habit.is_active == True
        )
    )
    habits_count = r.scalar() or 0
    m.habits_created = habits_count

    # Referrals
    r = await session.execute(
        select(func.count()).select_from(Referral).where(Referral.referrer_id == user_id)
    )
    m.invited_friends = r.scalar() or 0

    # Subscription months
    sub_months = 0
    if user and user.premium_until:
        pu = user.premium_until
        if pu.tzinfo is None:
            pu = pu.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if pu > now:
            sub_months = max(1, (pu - now).days // 30)
    m.subscription_months = sub_months

    # Completions today, last 7, last 30
    r = await session.execute(
        select(func.count()).select_from(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.status == "done",
            HabitLog.log_date == today,
        )
    )
    m.completions_today = r.scalar() or 0

    d7 = today - timedelta(days=7)
    r = await session.execute(
        select(func.count()).select_from(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.status == "done",
            HabitLog.log_date >= d7,
        )
    )
    m.completions_last_7_days = r.scalar() or 0

    d30 = today - timedelta(days=30)
    r = await session.execute(
        select(func.count()).select_from(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.status == "done",
            HabitLog.log_date >= d30,
        )
    )
    m.completions_last_30_days = r.scalar() or 0

    # Streak: consecutive days with at least one done (desc from today)
    r = await session.execute(
        select(HabitLog.log_date)
        .where(HabitLog.user_id == user_id, HabitLog.status == "done")
        .distinct()
        .order_by(HabitLog.log_date.desc())
    )
    done_dates = sorted(set(row[0] for row in r.all()), reverse=True)
    streak_days = 0
    prev = None
    for d in done_dates:
        if prev is None or (prev - d).days == 1:
            streak_days += 1
            prev = d
        else:
            break
    m.streak_days = streak_days

    # Streak no misses: consecutive days with no skips
    r = await session.execute(
        select(HabitLog.log_date)
        .where(HabitLog.user_id == user_id, HabitLog.status == "skipped")
        .distinct()
    )
    skip_dates = set(row[0] for row in r.all())
    streak_no_misses = 0
    d = today
    for _ in range(365):
        if d in skip_dates:
            break
        r2 = await session.execute(
            select(func.count()).select_from(HabitLog).where(
                HabitLog.user_id == user_id, HabitLog.status == "done", HabitLog.log_date == d
            )
        )
        if (r2.scalar() or 0) > 0:
            streak_no_misses += 1
        d -= timedelta(days=1)
    m.streak_no_misses = streak_no_misses

    # Perfect day: all active habits have at least one done log that day
    async def is_perfect_day(d: date) -> bool:
        r_habits = await session.execute(
            select(Habit.id).where(Habit.user_id == user_id, Habit.is_active == True)
        )
        habit_ids = [row[0] for row in r_habits.all()]
        if not habit_ids:
            return False
        for hid in habit_ids:
            r_done = await session.execute(
                select(func.count()).select_from(HabitLog).where(
                    HabitLog.habit_id == hid,
                    HabitLog.user_id == user_id,
                    HabitLog.status == "done",
                    HabitLog.log_date == d,
                )
            )
            if (r_done.scalar() or 0) == 0:
                return False
        return True

    m.all_habits_completed_today = await is_perfect_day(today) if habits_count > 0 else False
    m.all_habits_completed_7_days = True
    for i in range(7):
        d = today - timedelta(days=i)
        if not await is_perfect_day(d):
            m.all_habits_completed_7_days = False
            break

    # Perfect days total and streak
    perfect_dates = []
    for d in done_dates:
        if await is_perfect_day(d):
            perfect_dates.append(d)
    m.perfect_days_total = len(perfect_dates)
    perfect_streak = 0
    prev = None
    for d in perfect_dates:
        if prev is None or (prev - d).days == 1:
            perfect_streak += 1
            prev = d
        else:
            break
    m.perfect_days_streak = perfect_streak

    # Perfect weeks in current month
    now = _user_now(user) if user else datetime.now()
    month_start = date(now.year, now.month, 1)
    perfect_weeks = 0
    for w in range(5):
        week_start = month_start + timedelta(days=w * 7)
        if week_start.month != now.month:
            break
        week_perfect = True
        for d in range(7):
            d_date = week_start + timedelta(days=d)
            if d_date > today or d_date.month != now.month:
                break
            if not await is_perfect_day(d_date):
                week_perfect = False
                break
        if week_perfect and (week_start + timedelta(days=6)).month == now.month:
            perfect_weeks += 1
    m.perfect_weeks_in_month = perfect_weeks

    # Returned after miss: if user had 5+ days of skips then came back
    if skip_dates and done_dates:
        last_skip = max(skip_dates)
        last_done = done_dates[0]
        if last_done > last_skip:
            gap = (last_done - last_skip).days
            if gap >= 5:
                m.returned_after_miss_days = gap
    else:
        m.returned_after_miss_days = 0

    # MULTI_FOCUS: 5+ habits completed each day for 14 days - min count over 14 days
    min_habits = 999
    for i in range(14):
        d = today - timedelta(days=i)
        r_h = await session.execute(
            select(func.count(func.distinct(HabitLog.habit_id)))
            .select_from(HabitLog)
            .where(
                HabitLog.user_id == user_id,
                HabitLog.status == "done",
                HabitLog.log_date == d,
            )
        )
        cnt = r_h.scalar() or 0
        min_habits = min(min_habits, cnt)
    m.habits_completed_daily = min_habits if min_habits >= 5 else 0

    await session.flush()
    return m


async def recalculate_all_metrics(session: AsyncSession, bot=None) -> None:
    """Recalc metrics for all users. Called by daily job."""
    r = await session.execute(select(User))
    users = r.scalars().unique().all()
    for user in users:
        try:
            await recalculate_user_metrics(session, user.id, user)
        except Exception as e:
            logger.warning("Recalc metrics failed user=%s: %s", user.id, e)
    await session.flush()


async def update_metrics_on_habit_done(
    session: AsyncSession, user_id: int, user: User, today: date
) -> UserMetrics:
    """Incremental update after habit completed. Then full recalc for accuracy."""
    return await recalculate_user_metrics(session, user_id, user)


async def update_metrics_on_habit_created(
    session: AsyncSession, user_id: int, user: User
) -> UserMetrics:
    return await recalculate_user_metrics(session, user_id, user)


async def update_metrics_on_referral(
    session: AsyncSession, user_id: int, user: User
) -> UserMetrics:
    return await recalculate_user_metrics(session, user_id, user)


async def update_metrics_on_subscription(
    session: AsyncSession, user_id: int, user: User
) -> UserMetrics:
    return await recalculate_user_metrics(session, user_id, user)


def metrics_to_dict(m: UserMetrics, user: User | None = None) -> dict:
    """Convert UserMetrics to dict for achievement condition evaluation."""
    return {
        "habits_created": m.habits_created,
        "completed_total": m.total_completions,
        "streak_days": m.streak_days,
        "referrals_count": m.invited_friends,
        "subscription_months": m.subscription_months,
        "profile_completed": bool(user and user.timezone and user.timezone != "UTC"),
        "reminders_configured": m.habits_created >= 1,
        "all_habits_one_day": m.all_habits_completed_today,
        "all_habits_monday": m.all_habits_completed_today and (
            (_user_now(user).weekday() == 0) if user else False
        ),
        "no_skips_days": m.streak_no_misses,
        "returned_after_skip_days": m.returned_after_miss_days,
        "perfect_day_count": m.perfect_days_total,
        "perfect_streak": m.perfect_days_streak,
        "all_habits_7_days": m.all_habits_completed_7_days,
        "perfect_weeks_in_month": m.perfect_weeks_in_month,
        "completed_one_day": m.completions_today,
        "completed_7_days": m.completions_last_7_days,
        "completed_month": m.completions_last_30_days,
        "habit_changed_streak_ok": m.habit_modified and m.streak_preserved,
        "habit_goal_increased": m.habit_goal_increased,
        "five_habits_14_days": m.habits_completed_daily >= 5 and m.streak_days >= 14,
        "three_categories_30_days": m.active_categories >= 3 and m.streak_days >= 30,
        "new_habit_7_days": m.new_habit_streak >= 7,
        "referrals_streak_7": m.friends_with_7_day_streak,
        "synced_with_friend_14": m.sync_with_friend_streak >= 14,
        "referrals_active_30": m.active_friends_30_days,
    }


async def reset_flexibility_flags(session: AsyncSession, user_id: int) -> None:
    """Reset habit_modified and streak_preserved after FLEXIBILITY unlock."""
    m = await session.get(UserMetrics, user_id)
    if m:
        m.habit_modified = False
        m.streak_preserved = False
        await session.flush()


async def reset_growth_flag(session: AsyncSession, user_id: int) -> None:
    """Reset habit_goal_increased after GROWTH unlock."""
    m = await session.get(UserMetrics, user_id)
    if m:
        m.habit_goal_increased = False
        await session.flush()


async def mark_habit_modified(session: AsyncSession, user_id: int, user: User) -> None:
    """Call after habit edit. Sets habit_modified, recalc, then streak_preserved if streak intact."""
    m = await get_or_create_metrics(session, user_id)
    m.habit_modified = True
    await session.flush()
    await recalculate_user_metrics(session, user_id, user)
    m = await session.get(UserMetrics, user_id)
    if m and m.streak_days > 0:
        m.streak_preserved = True
    await session.flush()


async def mark_habit_goal_increased(session: AsyncSession, user_id: int) -> None:
    """Call when user increases habit goal (e.g. adds more days/times)."""
    m = await get_or_create_metrics(session, user_id)
    m.habit_goal_increased = True
    await session.flush()
