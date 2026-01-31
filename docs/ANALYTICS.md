# Analytics & Metrics

## Архитектура

- **Scheduler** (каждый час) выполняет тяжёлые SQL-агрегации и пишет в `analytics_metrics`
- **Admin dashboard** читает из кеша — без real-time запросов
- **AnalyticsService** — расчёт и кеширование
- **AnalyticsRepository** — raw SQL, upsert в кеш

## Формулы

### DAU (Daily Active Users)

```
DAU(d) = COUNT(DISTINCT user_id) 
         WHERE habit_logs.log_date = d
         JOIN habits ON habit_id
```

Пользователь считается активным, если в день `d` залогировал привычку (done или declined).

### WAU (Weekly Active Users)

```
WAU(end_date) = COUNT(DISTINCT user_id)
                WHERE habit_logs.log_date IN [end_date - 6d, end_date]
```

### MAU (Monthly Active Users)

```
MAU(end_date) = COUNT(DISTINCT user_id)
                WHERE habit_logs.log_date IN [end_date - 29d, end_date]
```

### Trial → Paid Conversion

```
trial_ended = COUNT(users WHERE tier IN ('free', 'premium'))
paid = COUNT(DISTINCT user_id FROM subscriptions WHERE payment_id IS NOT NULL)
conversion_pct = paid / trial_ended * 100
```

Пользователи, завершившие trial (free или premium), и из них — оплатившие.

### Churn

```
expired_30d = COUNT(subscriptions WHERE expires_at IN [now-30d, now])
active_now = COUNT(subscriptions WHERE is_active AND expires_at > now)
churn_pct = expired_30d / (active_now + expired_30d) * 100
```

Упрощённый churn: доля отписок за 30 дней.

### Habit Completion Rate

```
completed = COUNT(habit_logs WHERE completed = true AND log_date >= 30d_ago)
total = COUNT(habit_logs WHERE log_date >= 30d_ago)
completion_pct = completed / total * 100
```

Доля выполненных привычек от общего числа логов за 30 дней.

## Кеширование

| Ключ | Описание |
|------|----------|
| dau | int |
| wau | int |
| mau | int |
| trial_conversion | {trial_ended, paid, conversion_pct} |
| churn | {expired_30d, active_now, churn_pct} |
| completion_rate | {completed, total, completion_pct} |
| analytics_aggregate | все метрики в одном JSON |

## Scheduler

- Job: `analytics_refresh`
- Interval: 1 час
- Idempotent: перезапись кеша
