# Load & Chaos Testing — подготовка к нагрузке и сбоям

## 1. Load Testing — сценарии

### 1.1 Telegram bot handlers

| # | Сценарий | Метрики | Ожидаемое поведение |
|---|----------|---------|---------------------|
| L1 | Бурст /start — 100 пользователей одновременно | latency p95, ошибки | ThrottlingMiddleware отсекает >30/min на user. Ответ <2s. |
| L2 | Массовые callback (habit_done) — 50/sec | DB connections, scheduler load | Pool (5+10) выдерживает. Job coalesce срабатывает. |
| L3 | Admin dashboard — 10 админов кликают Analytics | DB query time | Чтение из analytics_metrics <100ms. |
| L4 | Долгий сценарий — 20 FSM flows параллельно | session duration, memory | Нет утечек. FSM cleanup при cancel. |

### 1.2 Scheduler jobs

| # | Сценарий | Метрики | Ожидаемое поведение |
|---|----------|---------|---------------------|
| L5 | habit_reminders — 10k habits в одно время | job duration, Telegram API 429 | Idempotent. При 429 — retry с backoff. |
| L6 | analytics_refresh — тяжёлые SQL | lock time, DB CPU | Запросы <30s. Не блокирует другие jobs. |
| L7 | health_check каждые 5 min | false positives | DB check <500ms. Bot getMe <1s. |

### 1.3 Payment flows

| # | Сценарий | Метрики | Ожидаемое поведение |
|---|----------|---------|---------------------|
| L8 | create_payment — 20 concurrent | YooKassa/Crypto Pay latency | Idempotency защищает от дублей. Timeout 30s. |
| L9 | Webhooks — 50 callbacks/min | DB write, response time | process_webhook <3s. 200 OK. Idempotent. |
| L10 | Balance top-up + subscription в одном окне | race conditions | FK, unique constraints. Нет double-credit. |

### 1.4 Health endpoint

| # | Сценарий | Метрики | Ожидаемое поведение |
|---|----------|---------|---------------------|
| L11 | GET /health — 100 req/s | 200/503, latency | <200ms при healthy. 503 при DB down. |

---

## 2. Chaos Testing — сценарии

### 2.1 Инфраструктура

| # | Сценарий | Действие | Ожидаемое поведение |
|---|----------|----------|---------------------|
| C1 | DB недоступна | `docker stop postgres` / блокировка сети | Health 503. Admin alert critical. Scheduler jobs fail, логируются. Bot handlers — UserContextMiddleware rollback. Recovery alert при восстановлении. |
| C2 | PostgreSQL restart | кратковременный disconnect | pool_pre_ping восстанавливает. Возможны единичные ошибки — retry на уровне вызова. |
| C3 | Scheduler stop | `scheduler.shutdown()` | Health 503 (scheduler not running). Alert warning. Bot работает. |
| C4 | Telegram API недоступен | блокировка api.telegram.org | getMe fail → health 503. Bot polling fail → shutdown. Admin alert. |

### 2.2 Платежи

| # | Сценарий | Действие | Ожидаемое поведение |
|---|----------|----------|---------------------|
| C5 | YooKassa timeout | simulate slow API | create_payment → error. Payment status=failed. Пользователь видит ошибку, может повторить. |
| C6 | Webhook при недоступной DB | DB down + webhook приходит | 500/503. Провайдер retry webhook. При восстановлении — повторная доставка. |
| C7 | Дубликат webhook | дважды тот же payload | Idempotent: второй раз — 200 OK, без double-credit. |
| C8 | Webhook с неверной подписью | поддельный payload | verify_webhook → false. 400. Не обрабатываем. |

### 2.3 Пользовательские сценарии

| # | Сценарий | Действие | Ожидаемое поведение |
|---|----------|----------|---------------------|
| C9 | User blocked bot | Forbidden при send_message | NotificationService catch, return False. log_job_skip. Не падает job. |
| C10 | FSM timeout / stale state | пользователь вернулся через день | /start сбрасывает FSM. Нет застревания. |
| C11 | Rate limit exceeded | 31 сообщение за минуту | ThrottlingMiddleware — handler не вызывается. Без ответа (можно добавить "Слишком много запросов"). |

---

## 3. Ожидаемое поведение системы

| Компонент | При сбое | Восстановление |
|-----------|----------|----------------|
| DB | 503 health, alert critical, rollback | pool_pre_ping, reconnect |
| Scheduler | alert warning, jobs не выполняются | restart → jobs из JobStore |
| Bot | polling exception → shutdown | restart → продолжение |
| Payment provider | Payment failed, error пользователю | retry при повторной попытке |
| Webhook | 5xx → провайдер retry | идемпотентность при retry |
| Notification | send_message fail → skip, log | следующий job попробует снова |

---

## 4. Admin alerts — проверка

| Событие | Severity | Cooldown | Источник |
|---------|----------|----------|----------|
| DB down | critical | 5 min | health_check job |
| Scheduler stop | warning | 15 min | health_check job |
| Bot unreachable | critical | 5 min | health_check job |
| DB recovered | info | — | recovery notification |
| Webhook verify fail | — | (добавить в payment_service) | process_webhook |

**Рекомендация:** В HTTP-handler webhook при `process_webhook` → `(False, "Verification failed")` вызвать:
```python
alert_svc = AdminAlertService(bot)
await alert_svc.send_alert(
    AlertSeverity.CRITICAL, "payment_webhook",
    "YooKassa/CryptoBot verification failed", details={"provider": provider}
)
```

---

## 5. Узкие места (bottlenecks)

| # | Узкое место | Риск | Рекомендация |
|---|-------------|------|--------------|
| B1 | DB connection pool (5+10) | При 20+ concurrent handlers — ожидание соединения | Увеличить pool_size до 10, max_overflow 20. Мониторить pool status. |
| B2 | Single event loop | Health check + polling + scheduler + aiohttp — всё в одном loop | При росте — вынести health на отдельный процесс или использовать lightweight check. |
| B3 | ThrottlingMiddleware in-memory | При multi-instance — каждый инстанс свой лимит | Для scale-out: Redis-based rate limit. |
| B4 | Scheduler JobStore — PostgreSQL | Блокировки при concurrent job execution | max_instances=1, coalesce=True уже есть. Misfire 300s. |
| B5 | Analytics SQL — тяжёлые COUNT/DISTINCT | Блокирует другие запросы при больших таблицах | Запуск раз в час. Рассмотреть материализованные представления. |
| B6 | Payment provider API | YooKassa/Crypto — сетевой вызов | ✅ Retry 3x с exponential backoff добавлен. |
| B7 | NotificationService send_message | При 429 (Too Many Requests) — падение | ✅ Retry с TelegramRetryAfter.retry_after. |
| B8 | aiogram long-polling | При большой нагрузке — задержки получения updates | Рассмотреть webhook для высоконагруженных ботов. |

---

## 6. Retry и backoff — где добавить

| Место | Текущее | Рекомендация |
|-------|---------|--------------|
| YooKassa create_payment | ✅ Retry 3x, backoff 1s, 2s, 4s | — |
| CryptoBot create_payment (httpx) | ✅ Retry 3x при timeout/ConnectError | — |
| NotificationService send_message | ✅ Retry 3x при 429 (TelegramRetryAfter) | — |
| PaymentService process_webhook | — | Не retry — идемпотентность на стороне провайдера |
| DB session | — | pool_pre_ping уже есть. Retry на уровне SQL — опционально. |
| init_db (startup) | Один вызов | Retry 3x с backoff при connection refused |

---

## 7. Рекомендации по оптимизации

1. **DB:** Увеличить pool, добавить `statement_timeout` для защиты от долгих запросов.
2. **Payments:** Retry для create_payment во всех провайдерах.
3. **Notifications:** Retry при 429, маркировка is_blocked при Forbidden.
4. **Health:** При DB fail — быстрый 503 без долгого hang.
5. **Logging:** Структурированный лог (JSON) для парсинга в Loki/Datadog.
6. **Metrics:** Экспорт Prometheus-метрик (request count, latency, errors) — отдельная задача.
7. **Webhook alerts:** Admin alert при verification failed.
