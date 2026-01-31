"""Profile and settings keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.timezone import TIMEZONE_BY_REGION, TIMEZONE_REGIONS, format_timezone_display


def profile_keyboard() -> InlineKeyboardMarkup:
    """Main profile buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Мои привычки", callback_data="profile_habits"),
                InlineKeyboardButton(text="📊 Детальный прогресс", callback_data="profile_detail_progress"),
            ],
            [
                InlineKeyboardButton(text="🏆 Достижения", callback_data="profile_achievements"),
                InlineKeyboardButton(text="📆 Календарь", callback_data="profile_calendar"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="profile_settings"),
                InlineKeyboardButton(text="👥 Пригласить друга", callback_data="profile_invite"),
            ],
            [InlineKeyboardButton(text="💳 Подписка", callback_data="profile_subscription")],
        ]
    )


def achievements_keyboard(achievements: list, unlocked_ids: set[int], is_premium: bool) -> InlineKeyboardMarkup:
    """Achievements list — each as button for premium lock click."""
    from app.texts import ACHIEVEMENTS_BACK
    buttons = []
    for a in achievements:
        status = "✅" if a.id in unlocked_ids else ("🔒" if a.is_premium and not is_premium else "🔒")
        text = f"{a.icon} {a.title} {status}"
        if a.is_premium and not is_premium and a.id not in unlocked_ids:
            buttons.append([InlineKeyboardButton(text=text, callback_data=f"ach_lock:{a.id}")])
        else:
            buttons.append([InlineKeyboardButton(text=text, callback_data="ach:noop")])
    buttons.append([InlineKeyboardButton(text=ACHIEVEMENTS_BACK, callback_data="achievements_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def achievement_reward_keyboard() -> InlineKeyboardMarkup:
    """New achievement reward."""
    from app.texts import ACHIEVEMENT_TO_ACHIEVEMENTS
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ACHIEVEMENT_TO_ACHIEVEMENTS, callback_data="achievement_reward_ok")],
        ]
    )


def achievement_premium_keyboard() -> InlineKeyboardMarkup:
    """Premium achievement locked."""
    from app.texts import ACHIEVEMENT_PREMIUM_CTA
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ACHIEVEMENT_PREMIUM_CTA, callback_data="balance_topup")],
        ]
    )


def calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Calendar month nav + day buttons."""
    from calendar import monthrange
    from app.texts import CALENDAR_BACK

    first_day, num_days = monthrange(year, month)
    week_start = (first_day - 6) % 7
    buttons = []
    row = []
    for _ in range(week_start):
        row.append(InlineKeyboardButton(text="·", callback_data="cal:noop"))
    for d in range(1, num_days + 1):
        row.append(InlineKeyboardButton(text=str(d), callback_data=f"calday:{year}:{month}:{d}"))
        if len(row) == 7:
            buttons.append(row)
            row = []
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(text="·", callback_data="cal:noop"))
        buttons.append(row)
    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1
    buttons.append([
        InlineKeyboardButton(text="◀️", callback_data=f"cal:{prev_y}:{prev_m}"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal:{next_y}:{next_m}"),
    ])
    buttons.append([InlineKeyboardButton(text=CALENDAR_BACK, callback_data="calendar_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def calendar_day_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Back from day to calendar."""
    from app.texts import CALENDAR_BACK
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=CALENDAR_BACK, callback_data=f"cal:{year}:{month}")],
        ]
    )


def paywall_keyboard() -> InlineKeyboardMarkup:
    """Paywall CTA."""
    from app.texts import PAYWALL_CTA_BUY, PAYWALL_CTA_LATER
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=PAYWALL_CTA_BUY, callback_data="balance_topup"),
                InlineKeyboardButton(text=PAYWALL_CTA_LATER, callback_data="paywall_later"),
            ],
        ]
    )


def progress_blocker_keyboard() -> InlineKeyboardMarkup:
    """Progress blocker for free users."""
    from app.texts import PROGRESS_BLOCKER_CTA
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=PROGRESS_BLOCKER_CTA, callback_data="balance_topup")],
        ]
    )


def streak_lost_keyboard() -> InlineKeyboardMarkup:
    """Streak lost retention."""
    from app.texts import STREAK_LOST_CTA
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=STREAK_LOST_CTA, callback_data="balance_topup")],
        ]
    )


def detail_progress_keyboard() -> InlineKeyboardMarkup:
    """Detail progress screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="detail_progress_back")],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    """Settings screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏰ Изменить часовой пояс", callback_data="settings_timezone")],
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_back")],
        ]
    )


def timezone_method_keyboard() -> InlineKeyboardMarkup:
    """Choose timezone input method."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌍 По региону", callback_data="tz_method:region"),
                InlineKeyboardButton(text="⌨️ Вручную", callback_data="tz_method:manual"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="tz_back")],
        ]
    )


def timezone_region_keyboard() -> InlineKeyboardMarkup:
    """Choose region (Europe, Asia, etc)."""
    buttons = []
    for region_id, label in TIMEZONE_REGIONS.items():
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"tz_region:{region_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="tz_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timezone_list_keyboard(region_id: str, selected_tz: str | None = None) -> InlineKeyboardMarkup:
    """List of timezones in region. selected_tz = currently selected for checkmark."""
    tz_list = TIMEZONE_BY_REGION.get(region_id, [])
    buttons = []
    for tz in tz_list:
        prefix = "✅ " if tz == selected_tz else ""
        display = format_timezone_display(tz)
        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix}{display}",
                callback_data=f"tz_select:{tz}",
            ),
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="tz_region_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
