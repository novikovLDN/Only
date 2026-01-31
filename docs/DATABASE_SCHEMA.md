# Database Schema — Production Design

## 1. Схема таблиц и связи

```
users
  ├── habits (1:N)
  │     ├── habit_schedules (1:N)
  │     └── habit_logs (1:N)
  │           └── habit_decline_notes (N:1, optional)
  ├── balances (1:1)
  ├── balance_transactions (1:N)
  ├── payments (1:N)
  ├── subscriptions (1:N)
  │     └── payments (N:1, optional)
  ├── referrals (as referrer, as referred)
  └── referred_by → users (N:1)

system_logs (standalone)
admin_alerts (standalone)
```

## 2. Порядок создания таблиц (для migrations)

```
1. users
2. habits
3. habit_schedules
4. habit_decline_notes
5. habit_logs
6. balances
7. payments
8. balance_transactions
9. subscriptions
10. referrals
11. system_logs
12. admin_alerts
```

## 3. Индексы для аналитики

| Таблица | Индексы | Назначение |
|---------|---------|------------|
| users | telegram_id (unique), referral_code (unique), created_at | Поиск, аналитика по когортам |
| habit_logs | (habit_id, log_date) unique | Дедупликация, отчёты |
| habit_logs | (user_id via habit, log_date) | Аналитика по пользователю |
| payments | provider_payment_id, idempotency_key, created_at | Idempotency, revenue |
| balance_transactions | (user_id, created_at) | Audit trail |
| referrals | (referrer_id, referred_id) unique | Антифрод |
| system_logs | (fingerprint, created_at) | Дедупликация алертов |
| admin_alerts | (fingerprint, created_at) | Дедупликация |

## 4. Архитектурные риски

1. **subscriptions.payment_id → payments**: При refund/chargeback нужно обновлять subscription. Рекомендуется event-sourcing для платежей.
2. **habit_logs объём**: При >1M строк — партиционирование по log_date.
3. **system_logs объём**: Ротация или партиционирование по created_at.
4. **Balance vs balance_transactions**: Денормализация (balance.amount) для производительности. Сумма должна = SUM(transactions) — проверять периодически.
5. **User.id = telegram_id**: Упрощает связки, но при миграции на другую систему — риск. Рекомендуется внутренний UUID для users.
6. **decline_notes → habit_decline_notes**: Переименование таблицы. Миграция с данными: CREATE new, INSERT SELECT, DROP old.

---

## 5. Структура migrations

```
migrations/
├── env.py
├── script.py.mako
└── versions/
    ├── 001_initial_schema.py      # Все таблицы
    └── 002_add_balance_transactions.py  # Если добавляем позже
```

Порядок создания в миграции (для avoid FK violations):

```python
# 001
op.create_table("users", ...)
op.create_table("habits", ...)
op.create_table("habit_schedules", ...)
op.create_table("habit_decline_notes", ...)
op.create_table("habit_logs", ...)
op.create_table("balances", ...)
op.create_table("payments", ...)
op.create_table("balance_transactions", ...)
op.create_table("subscriptions", ...)
op.create_table("referrals", ...)
op.create_table("system_logs", ...)
op.create_table("admin_alerts", ...)
```
