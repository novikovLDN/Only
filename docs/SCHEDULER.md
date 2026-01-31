# Scheduler

## Архитектура

- **AsyncIOScheduler** — async event loop
- **SQLAlchemyJobStore** (PostgreSQL) — персистентность jobs
- **Job IDs** — детерминированные: habit_reminders, trial_notifications, subscription_notifications, health_check

## Job registration API

```python
from app.scheduler import add_job, remove_job, update_job
from app.scheduler.registry import JOB_HABIT_REMINDERS
from apscheduler.triggers.interval import IntervalTrigger

# Добавить
add_job(run_habit_reminders_job, IntervalTrigger(minutes=5), JOB_HABIT_REMINDERS, args=(bot,))

# Удалить
remove_job(JOB_HABIT_REMINDERS)

# Обновить trigger
update_job(JOB_HABIT_REMINDERS, trigger=IntervalTrigger(minutes=10))
```

## Jobs

| Job ID | Интервал | Описание |
|--------|----------|----------|
| habit_reminders | 5 min | Напоминания привычек (timezone-aware) |
| trial_notifications | 1 h | Trial: -24h, -3h, expired |
| subscription_notifications | 1 h | Подписка: -3d, -24h, -3h, expired |
| health_check | 5 min | DB + scheduler status |

## Idempotency

- Каждый job проверяет актуальный статус перед действием
- `_should_notify_user()` — не заблокирован
- Trial/Subscription — проверка `expires_at`, `is_active`

## Логирование

- `job_execution_log` — start, duration, success/error
- `log_job_skip` — пропуски (user_blocked, error)

## Graceful shutdown

```python
await shutdown_scheduler()  # wait=True — дожидается завершения running jobs
```
