# Operational Playbook — HabitBot

Практичный runbook для инцидентов и восстановления.

---

## 1. Типовые инциденты

### 1.0 UndefinedColumnError / Schema drift (CRITICAL)

| | |
|---|---|
| **Симптомы** | `asyncpg.exceptions.UndefinedColumnError: column users.notifications_enabled does not exist`, scheduler crashes every 5 min, middleware crashes on every update, bot DOWN |
| **Причины** | ORM model ahead of DB schema; migration not applied; deploy without alembic upgrade |
| **Проверка** | `psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='notifications_enabled'"` |

**Шаги решения:**

1. **Deploy order (CRITICAL):**
   - Deploy code with schema guards, middleware fail-safe, scheduler circuit breaker
   - Run `alembic upgrade head` in production (or let deploy_gate do it)
   - Restart application
2. **If deploy gate fails:** fix migration, ensure 007 is applied
3. **Verification:**
   - `SELECT notifications_enabled FROM users LIMIT 1;`
   - Bot responds to `/start`
   - No CRITICAL logs repeating
   - Scheduler starts successfully

**Guards in place:**
- Schema mismatch → DEGRADED mode (scheduler disabled, bot runs with minimal user)
- Deploy gate: `python scripts/deploy_gate.py` before app start
- Middleware: minimal in-memory user on schema error
- Scheduler: circuit breaker on schema error

---

### 1.1 Database недоступна

| | |
|---|---|
| **Симптомы** | Health 503, алерт `[CRITICAL] health_check database`, handlers не отвечают, ошибки подключения в логах |
| **Причины** | PostgreSQL restart, сеть, исчерпан pool, диск/память на хосте БД |
| **Проверка** | `psql $DATABASE_URL -c "SELECT 1"` |

**Шаги решения:**

1. Проверить статус PostgreSQL (Railway dashboard / хост).
2. Проверить `DATABASE_URL`, сетевую доступность.
3. Если restart — подождать 1–2 мин, `pool_pre_ping` восстановит соединения.
4. Если pool исчерпан — перезапустить бота (освободит соединения).
5. Если БД на стороне провайдера — проверить статус-страницу.

---

### 1.2 Bot не отвечает / Telegram API недоступен

| | |
|---|---|
| **Симптомы** | Health 503 (bot fail), пользователи не получают ответы, `TelegramServerError`, `ConnectionError` в логах |
| **Причины** | Telegram outage, сеть, неверный BOT_TOKEN, блокировка |
| **Проверка** | `curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe"` |

**Шаги решения:**

1. Проверить https://status.telegram.org.
2. Убедиться, что `BOT_TOKEN` корректен.
3. Проверить сеть из контейнера/хоста (DNS, firewall).
4. При длительном outage — дождаться восстановления, бот продолжит polling после reconnect.
5. Перезапустить контейнер при зависании getUpdates.

---

### 1.3 Scheduler не запущен / jobs не выполняются

| | |
|---|---|
| **Симптомы** | Алерт `[WARNING] health_check scheduler`, нет напоминаний, нет trial/subscription уведомлений |
| **Причины** | Ошибка при init, JobStore lock, исключение в job |
| **Проверка** | Логи `Scheduler started`, `Job added`, ошибки в `job_execution_log` |

**Шаги решения:**

1. Проверить логи на `Scheduler initialized`, `Job failed`.
2. Проверить таблицу `apscheduler_jobs` — есть ли записи.
3. При блокировке JobStore — проверить долгие транзакции в БД.
4. Перезапустить бота — scheduler поднимется заново, jobs восстановятся из JobStore.
5. Если job падает — проверить причину (DB, bot send_message) и починить.

---

### 1.4 Платежи не проходят (webhook)

| | |
|---|---|
| **Симптомы** | Оплата прошла у провайдера, баланс/подписка не обновились; в логах нет `Payment completed` |
| **Причины** | Webhook endpoint не настроен/недоступен, verify failed, ошибка в process_webhook |
| **Проверка** | Логи webhook, таблица `payments` (status pending), логи провайдера |

**Шаги решения:**

1. Убедиться, что webhook URL доступен извне и принимает POST.
2. Проверить логи веб-сервера на запросы от YooKassa/CryptoBot.
3. Если `verify_webhook` failed — проверить secret, IP whitelist.
4. **Ручное завершение:** найти payment по `provider_payment_id` в БД, если оплата подтверждена у провайдера — вручную обновить `payments.status`, вызвать `_credit_balance` / `_activate_subscription` (через админ-скрипт или SQL + код).
5. Идемпотентность: повторная отправка webhook провайдером не создаст дубль.

---

### 1.5 Платежи не создаются (create_payment)

| | |
|---|---|
| **Симптомы** | Пользователь нажал «Оплатить» — ошибка или зависание; `create_payment failed` в логах |
| **Причины** | YooKassa/Crypto API недоступен, неверные credentials, timeout |
| **Проверка** | `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, `CRYPTOBOT_TOKEN` |

**Шаги решения:**

1. Проверить credentials в личном кабинете провайдера.
2. Проверить логи на `YooKassa retry`, `CryptoBot retry`, `TimeoutException`.
3. При 5xx от API — retry уже есть; если не помогает — проверить статус провайдера.
4. Payment остаётся в status=failed — пользователь может повторить попытку.

---

### 1.6 Health check timeout / Railway перезапускает контейнер

| | |
|---|---|
| **Симптомы** | Контейнер постоянно перезапускается, Railway показывает failed health |
| **Причины** | Health check >30s, deadlock, DB/bot check висит |
| **Проверка** | `curl -w "%{time_total}" http://localhost:$PORT/health` |

**Шаги решения:**

1. Убедиться, что health отвечает <10s.
2. Проверить, не блокируется ли event loop (тяжёлый sync код, долгий DB запрос).
3. Временно упростить health (только `SELECT 1`) для восстановления.
4. Увеличить `healthcheckTimeout` в railway.json при необходимости (не маскировать проблему).

---

### 1.7 Напоминания не приходят

| | |
|---|---|
| **Симптомы** | Пользователи не получают habit reminders в ожидаемое время |
| **Причины** | Scheduler не работает, job пропускает (timezone, `is_blocked`), 429 от Telegram |
| **Проверка** | Логи `habit_reminders: sent N`, `job skip`, `Telegram 429` |

**Шаги решения:**

1. Проверить, что scheduler running (health).
2. Проверить `habit_schedules.is_enabled`, `habits.is_active`, `users.is_blocked`.
3. Проверить timezone пользователя.
4. При 429 — NotificationService делает retry; при массовой рассылке возможны задержки.
5. Job выполняется каждые 5 мин — напоминание может прийти с задержкой до 5 мин.

---

### 1.8 Дублирование платежей / double credit

| | |
|---|---|
| **Симптомы** | Дважды зачислен баланс или две подписки за один платёж |
| **Причины** | Дублирование webhook, баг в idempotency check |
| **Проверка** | `payments` по `provider_payment_id`, `balance_transactions` |

**Шаги решения:**

1. Idempotency должна блокировать дубли — проверить логи `Idempotent: payment X already completed`.
2. Если дубль произошёл — ручной откат: отменить `BalanceTransaction` или продление подписки, связаться с пользователем.
3. Разобрать баг в `process_webhook` (проверка `existing` по `provider`+`provider_payment_id`).

---

### 1.9 Высокая нагрузка / 429 от Telegram

| | |
|---|---|
| **Симптомы** | Массовые 429, задержки доставки, `TelegramRetryAfter` в логах |
| **Причины** | Пиковая рассылка (habit_reminders), >30 msg/s |
| **Проверка** | Логи `Telegram 429`, количество habits/schedules |

**Шаги решения:**

1. Retry в NotificationService должен обрабатывать 429.
2. При постоянных 429 — снизить нагрузку: chunked processing, расширить временное окно reminders.
3. См. docs/SCALING_ARCHITECTURE.md — throttled sender, sharding.

---

### 1.10 Алерты не приходят в Telegram

| | |
|---|---|
| **Симптомы** | Инцидент есть, уведомление в ALERT_CHAT_ID не пришло |
| **Причины** | `ALERT_CHAT_ID` не задан, бот заблокирован в чате, ошибка в AdminAlertService |
| **Проверка** | Env `ALERT_CHAT_ID`, логи `Failed to send alert` |

**Шаги решения:**

1. Проверить `ALERT_CHAT_ID` в настройках деплоя.
2. Убедиться, что пользователь запускал бота (отправил /start) в чате алертов.
3. Проверить cooldown — повторный алерт с тем же fingerprint не уйдёт в течение интервала.
4. Проверить `admin_alerts` в БД — записываются ли отправленные алерты.

---

## 2. Recovery процедуры

### 2.1 Полный перезапуск сервиса

```
1. Railway: Deploy → Redeploy (или manual restart)
2. Либо: docker restart <container> / systemctl restart habitbot
3. Дождаться health 200 (обычно 10–30 сек)
4. Проверить логи: "Startup complete", "Scheduler started"
5. Проверить /admin — dashboard отвечает
```

### 2.2 Восстановление после потери БД (RPO/RTO)

```
1. Восстановить PostgreSQL из бэкапа (Railway/провайдер).
2. Проверить DATABASE_URL (при смене хоста).
3. alembic upgrade head (если схема могла измениться).
4. Перезапустить бота.
5. Проверить последние payments, subscriptions — согласованность с провайдерами.
```

### 2.3 Ручное завершение платежа (webhook не дошёл)

```sql
-- 1. Найти payment
SELECT id, user_id, amount, payment_type, provider, provider_payment_id, status
FROM payments
WHERE provider_payment_id = '<id_from_provider>' AND status = 'pending';

-- 2. Подтвердить оплату в личном кабинете YooKassa/CryptoBot
-- 3. Выполнить зачисление через админ-скрипт или вручную:
--    - balance_topup: INSERT balance_transaction, UPDATE balances
--    - subscription: INSERT subscriptions, UPDATE users SET tier='premium'
-- 4. UPDATE payments SET status='succeeded', completed_at=NOW() WHERE id=...;
```

*(Рекомендуется вынести в отдельный скрипт `scripts/manual_complete_payment.py`)*

### 2.4 Сброс FSM для пользователя (застрял в диалоге)

```
Пользователь пишет /cancel или /start — FSM сбрасывается.
Если не помогает — MemoryStorage сбрасывается при рестарте бота.
При RedisStorage — удалить ключи redis для user_id (если есть такой скрипт).
```

### 2.5 Очистка зависших jobs (scheduler)

```
1. Перезапустить бота — scheduler пересоздастся, jobs из JobStore.
2. Если job постоянно падает — временно удалить из БД:
   DELETE FROM apscheduler_jobs WHERE id = 'habit_reminders';
   (после перезапуска job будет пересоздан setup_scheduler)
3. Либо исправить причину падения и перезапустить.
```

---

## 3. Escalation

| Уровень | Действие |
|---------|----------|
| L1 | Проверить health, логи, перезапустить |
| L2 | Разбор БД, платежей, ручное восстановление |
| L3 | Изменение кода, миграции, координация с провайдерами |

**Критичные инциденты (платежи, полная недоступность):** эскалировать немедленно.

---

## 4. Шаблон Postmortem

```markdown
# Postmortem: [Краткое название инцидента]

**Дата:** YYYY-MM-DD  
**Время начала:** HH:MM UTC  
**Время окончания:** HH:MM UTC  
**Длительность:** X ч Y мин  
**Автор:** имя

---

## Резюме

Одно-два предложения: что произошло и какой эффект.

## Влияние

- Затронутые компоненты:
- Затронутые пользователи (оценка):
- Потеря данных / финансовые потери (если есть):

## Хронология

| Время (UTC) | Событие |
|-------------|---------|
| HH:MM | Обнаружены симптомы (health 503 / алерт) |
| HH:MM | Начата диагностика |
| HH:MM | Выявлена причина |
| HH:MM | Применено исправление |
| HH:MM | Восстановление подтверждено |

## Корневая причина

Опишите техническую причину (например: PostgreSQL restart на стороне Railway, pool исчерпан).

## Решение / Восстановление

Что было сделано для устранения (перезапуск, ручное завершение платежей и т.п.).

## Действия для предотвращения

- [ ] Действие 1 (например: настроить алерт на pool exhaustion)
- [ ] Действие 2
- [ ] Действие 3

## Дополнительные материалы

- Ссылки на логи, дашборды, тикеты
```

---

## 5. Production deploy order (schema-safe)

```
1. Deploy code (with guards, deploy_gate in startCommand)
2. Start command runs: python scripts/deploy_gate.py && python run.py
   - deploy_gate: alembic upgrade head; verify current == heads
   - If mismatch → FAIL DEPLOY (exit 1)
3. App starts → bootstrap: check migrations, verify schema (notifications_enabled, timezone, tier)
4. If schema OK → scheduler starts; if mismatch → DEGRADED (bot runs, scheduler disabled)
5. Observe logs 15 min: NO UndefinedColumnError, scheduler started, bot answers
```

---

## 6. Полезные команды

```bash
# Health
curl -s http://localhost:$PORT/health | jq

# DB (локально)
psql $DATABASE_URL -c "SELECT 1"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users"

# Миграции
alembic upgrade head
alembic current
alembic heads

# Schema verification
psql $DATABASE_URL -c "SELECT notifications_enabled FROM users LIMIT 1"

# Логи (Railway)
railway logs -f
```
