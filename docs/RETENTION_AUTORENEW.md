# Retention & Autorenew

## SubscriptionRenewService

**Автопродление с баланса** — списание при истечении подписки.

| Метод | Описание |
|-------|----------|
| try_renew_from_balance(sub, user) | Списывает с баланса, продлевает подписку. Возвращает (success, error). |
| mark_renewal_attempted(sub) | Фиксирует неуспешную попытку (retry cooldown). |

**Условия:**
- `subscription.auto_renew_from_balance == True`
- Баланс >= сумма продления (sub.amount)
- Для retry: истекшая подписка, `last_renewal_attempt_at` старше 72ч

**Включение:** Для новых платных подписок — True. Существующие — False (миграция).

---

## RetentionService

| Метод | Описание |
|-------|----------|
| get_users_for_inactivity_reminder() | Пользователи без активности 3+ дней, cooldown 7 дней |
| get_users_for_streak_milestone() | Пользователи, достигшие 7, 14, 30, 60, 100 дней подряд |

**Защита от спама:**
- Inactivity: макс 1 раз в 7 дней
- Streak: 1 раз на каждый milestone (7, 14, 30, 60, 100)

---

## Scheduler Jobs

| Job | Интервал | Описание |
|-----|----------|----------|
| subscription_renew | 6 ч | Продление за 24ч до истечения + retry истекших (cooldown 72ч) |
| retention | 12 ч | Inactivity reminders, streak rewards |

---

## Миграция

`migrations/versions/003_retention_autorenew.py`:
- subscriptions: auto_renew_from_balance, last_renewal_attempt_at
- users: last_inactivity_reminder_at, last_streak_milestone
