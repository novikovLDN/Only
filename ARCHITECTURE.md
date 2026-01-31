# Архитектура бота отслеживания привычек

## Структура проекта (Clean Architecture)

```
OnlyBot/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Entry point
│   │
│   ├── config/                    # Configuration layer
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── constants.py
│   │
│   ├── models/                    # Domain/DB models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── habit.py
│   │   ├── habit_schedule.py
│   │   ├── habit_log.py
│   │   ├── decline_note.py
│   │   ├── subscription.py
│   │   ├── payment.py
│   │   ├── balance.py
│   │   ├── referral.py
│   │   └── system_log.py
│   │
│   ├── repositories/              # Data access layer (Repository pattern)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user_repo.py
│   │   ├── habit_repo.py
│   │   ├── subscription_repo.py
│   │   ├── payment_repo.py
│   │   ├── balance_repo.py
│   │   ├── referral_repo.py
│   │   └── system_log_repo.py
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── habit_service.py
│   │   ├── subscription_service.py
│   │   ├── notification_service.py
│   │   ├── referral_service.py
│   │   └── anti_fraud_service.py
│   │
│   ├── integrations/              # External integrations
│   │   ├── __init__.py
│   │   ├── payments/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── yookassa_provider.py
│   │   │   ├── telegram_stars_provider.py
│   │   │   └── cryptobot_provider.py
│   │   └── payment_service.py      # Unified payment facade
│   │
│   ├── handlers/                  # Presentation layer (aiogram handlers)
│   │   ├── __init__.py
│   │   ├── start.py
│   │   ├── habits.py
│   │   ├── settings.py
│   │   ├── payments.py
│   │   ├── referrals.py
│   │   └── admin.py
│   │
│   ├── fsm/                       # Finite State Machine
│   │   ├── __init__.py
│   │   ├── states.py
│   │   └── storage.py
│   │
│   ├── keyboards/                 # Inline/Reply keyboards
│   │   ├── __init__.py
│   │   ├── main_menu.py
│   │   ├── habits.py
│   │   ├── settings.py
│   │   ├── payments.py
│   │   └── admin.py
│   │
│   ├── middlewares/               # Middleware chain
│   │   ├── __init__.py
│   │   ├── throttle.py
│   │   ├── logging_mw.py
│   │   ├── user_context.py
│   │   └── antifraud.py
│   │
│   ├── scheduler/                 # Background jobs
│   │   ├── __init__.py
│   │   ├── jobs.py
│   │   └── notifications.py
│   │
│   ├── monitoring/                # Health & alerting
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── alerting.py
│   │   └── metrics.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       ├── formatters.py
│       ├── timezone.py
│       └── text.py
│
├── migrations/                    # Alembic migrations
│   └── versions/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── alembic.ini
├── pyproject.toml / setup.py
├── requirements.txt
├── Dockerfile
├── railway.json
├── .env.example
├── .gitignore
└── README.md
```

---

## FSM States (все пользовательские сценарии)

### Onboarding & Settings
| State Group | States |
|-------------|--------|
| **SettingsFSM** | waiting_timezone, waiting_notification_time |
| **OnboardingFSM** | greeting, waiting_language |

### Habits
| State Group | States |
|-------------|--------|
| **HabitFSM** | waiting_name, waiting_description, waiting_schedule_type, waiting_schedule_time, waiting_schedule_days, waiting_confirm |
| **HabitEditFSM** | selecting_habit, selecting_field, waiting_new_value |
| **HabitLogFSM** | selecting_habit, adding_note (decline note) |

### Payments & Subscriptions
| State Group | States |
|-------------|--------|
| **PaymentFSM** | selecting_amount, selecting_method, awaiting_webhook |
| **BalanceTopUpFSM** | selecting_amount, selecting_provider, processing |
| **SubscriptionFSM** | selecting_plan, selecting_payment, processing |

### Referrals
| State Group | States |
|-------------|--------|
| **ReferralFSM** | sharing_link |

### Admin
| State Group | States |
|-------------|--------|
| **AdminFSM** | main_menu, viewing_metrics, viewing_logs, broadcasting |

---

## Scheduler Jobs

### Habit Reminders
- Cron: по расписанию каждой привычки (timezone-aware)
- Action: отправка напоминания пользователю

### Trial Lifecycle
| Триггер | Timing |
|---------|--------|
| Trial started | +36h после старта |
| Mid-trial | +90h после старта |
| Expiry warning | -24h до окончания |
| Urgent warning | -3h до окончания |
| Trial expired | в момент истечения |

### Subscription Lifecycle
| Триггер | Timing |
|---------|--------|
| Renewal soon | -3 days |
| Expiry warning | -24h |
| Urgent | -3h |
| Expired | в момент истечения |

---

## Ограничения по тарифам

| Feature | Trial | Free | Premium |
|---------|-------|------|---------|
| Habits max | 3 | 5 | Unlimited |
| Notifications | ✅ | ✅ | ✅ |
| Custom times | Limited | Limited | Full |
| Referral rewards | No | Partial | Full |
| Export | No | No | Yes |
| Trial duration | 7 days | - | - |

---

## Риски и предупреждения

1. **Idempotency payments**: Обязательно хранить `idempotency_key` и проверять перед списанием
2. **Race conditions**: При начислении реферальных бонусов использовать транзакции и блокировки
3. **Timezone edge cases**: DST переходы — использовать `zoneinfo` (Python 3.9+)
4. **Scheduler scaling**: На Railway один инстанс — APScheduler подходит; при масштабировании нужен Redis-based scheduler (e.g. celery-beat)
5. **Admin alerts deduplication**: Кэшировать hash последней критической ошибки, не слать повторно 5 мин
