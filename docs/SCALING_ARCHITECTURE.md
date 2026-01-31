# Scaling Architecture — 1k → 10k → 100k пользователей

Взгляд scalability architect: bottlenecks, решения, этапы роста.

---

## 1. Анализ Bottlenecks

### 1.1 Scheduler

| Проблема | Описание | Пиковая нагрузка |
|----------|----------|------------------|
| **habit_reminders** | Загружает ВСЕ HabitSchedule за раз, итерация по рядам, send_message по одному | При 100k habits × 2 sched/user = 200k rows. Один job = один SELECT, потом N send_message |
| **Time window** | Job каждые 5 min, окно «час:минута ±5 мин» — в 09:00 могут совпасть тысячи | 10k users в 09:00 = 10k send_message за ~5 мин = 33 msg/s (на пределе лимита) |
| **JobStore lock** | SQLAlchemyJobStore — блокировки при записи в apscheduler_jobs | При частом misfire — конкуренция |
| **Single-threaded execution** | Все jobs в одном event loop | Долгий analytics_refresh блокирует habit_reminders |
| **Нет batching** | send_message по одному | Нет использования batch API (Telegram не даёт batch send) |

### 1.2 Telegram API Limits

| Лимит | Значение | Риск |
|-------|----------|------|
| Глобальный | ~30 msg/s на бота | habit_reminders в 09:00 — burst |
| Per-chat (private) | Фактически лимит общий | 1 user = 1 chat, много чатов — ок |
| 429 Retry-After | Секунды до разблокировки | Уже обрабатывается в NotificationService |
| sendMessage | 1 req = 1 msg | Batching недоступен |

### 1.3 Database

| Проблема | Текущее | При росте |
|----------|---------|-----------|
| Connection pool | 5 + 10 overflow = 15 | Handlers + jobs конкурируют. При 50 RPS — ожидание |
| habit_reminders query | SELECT * JOIN — все schedules | 200k rows = тяжёлый fetch, память |
| Analytics SQL | COUNT DISTINCT, агрегации | Блокирует другие запросы при больших таблицах |
| JobStore | Sync SQLAlchemy на PostgreSQL | Блокировки при misfire |

### 1.4 Другие

| Компонент | Bottleneck |
|-----------|------------|
| Throttling | In-memory — при 2+ инстансах лимиты не общие |
| FSM | MemoryStorage — при рестарте теряется, при 2 инстансах — рассинхрон |
| Long-polling | Один поток getUpdates — при 100k users задержки доставки |

---

## 2. Решения

### 2.1 Batching и Throttling отправки

**Проблема:** 10k сообщений за 5 мин = 33 msg/s. Лимит 30 msg/s.

**Решение: глобальный rate limiter для исходящих сообщений**

```python
# OutgoingMessageQueue / ThrottledNotifier
# Вместо немедленного send_message — очередь с rate limit ~25 msg/s
# asyncio.Queue + worker с asyncio.sleep(1/25) между сообщениями
```

**Плюсы:** Не превышаем лимит, плавная отправка.  
**Минусы:** Задержка доставки (при 10k — ~7 мин на всю очередь).

**Альтернатива: временное окно расширить**

- Вместо «09:00 ±5 мин» — «09:00–09:30» с рандомной задержкой внутри
- Снижает пик, распределяет нагрузку

### 2.2 Job grouping и разделение

**Проблема:** habit_reminders грузит всё сразу.

**Решение 1: Sharding по времени**

- Разбить job на N подзадач: `habit_reminders_shard_0` … `habit_reminders_shard_N`
- Каждый shard обрабатывает `user_id % N == shard_id`
- Запускать с offset 1–2 мин между shards

**Решение 2: Chunked processing**

- `LIMIT 1000 OFFSET ...` с пагинацией
- Или `WHERE (user_id % 10) = :shard` для параллельных воркеров
- Отправлять чанками с паузой между ними

**Решение 3: Вынести в отдельный worker**

- Bot instance: только handlers + health
- Worker instance: scheduler + NotificationService
- Разделение нагрузки на DB и CPU

### 2.3 Database

| Решение | Описание |
|---------|----------|
| Увеличить pool | pool_size=20, max_overflow=30 при 10k+ |
| Read replica | Analytics — readonly replica, тяжёлые SELECT туда |
| Индексы | habit_schedules (user_id, reminder_time), habit_logs (user_id, log_date) |
| Chunked queries | `yield_per(500)` для больших выборок |
| Отдельная сессия для jobs | Свой pool для scheduler, не конкурирует с handlers |

### 2.4 Throttling (входящий)

| Сейчас | Для scale-out |
|--------|----------------|
| In-memory, 30 req/min на user | Redis: `INCR` + `EXPIRE` по user_id |
| Per-process | Общий лимит для кластера |

---

## 3. Рекомендации по этапам

### 3.1 1k пользователей (~3k habits, ~1k schedules)

| Компонент | Рекомендация |
|-----------|--------------|
| Архитектура | Один инстанс, текущая схема |
| DB pool | 5+10 — достаточно |
| Scheduler | Интервалы как есть |
| Telegram | Пик ~50 msg в 5 мин — ок |
| FSM | MemoryStorage приемлемо |
| Throttling | In-memory ок |

**Действия:** Мониторинг, алерты. Ничего менять не обязательно.

---

### 3.2 10k пользователей (~30k habits, ~10k schedules)

| Компонент | Рекомендация |
|-----------|--------------|
| **Scheduler** | Добавить **throttled send**: максимум 25 msg/s, очередь |
| **habit_reminders** | Чанковать по 500–1000, пауза 20–40s между чанками |
| **DB** | pool_size=15, max_overflow=25 |
| **Analytics** | Вынести в ночной job или реже (раз в 6 ч) |
| **FSM** | RedisStorage — при планировании 2-го инстанса |
| **Throttling** | Redis — при 2+ инстансах |

**Критично:**
- ThrottledNotifier / OutgoingMessageQueue
- Chunked habit_reminders

**Оценка:** 10k reminders в 09:00 → ~7 мин при 25 msg/s. Приемлемо.

---

### 3.3 100k пользователей

| Компонент | Рекомендация |
|-----------|--------------|
| **Архитектура** | Разделить: Bot (handlers) + Worker (scheduler) |
| **Scheduler** | Отдельный процесс/контейнер, свой DB pool |
| **habit_reminders** | Sharding по user_id % 10, 10 jobs с offset 2 мин |
| **Telegram** | Рассмотреть webhook вместо long-polling |
| **DB** | Read replica для analytics, connection pooler (PgBouncer) |
| **Redis** | Обязательно: FSM, throttling, очередь сообщений |
| **Масштаб** | 2+ bot инстансов за load balancer (webhook) или 1 bot + 1 worker |

**Схема:**
```
[Users] → [Telegram] → [Bot LB] → [Bot 1, Bot 2]  (webhook)
                              ↘ [Worker] → Scheduler → Redis Queue → Telegram API
```

**Оценка:** 100k reminders → 100k/25 ≈ 67 мин. Нужно расширить окно (например 08:00–10:00) или приоритизировать по engagement.

---

## 4. Что выносить отдельно при росте

### 4.1 При 10k

| Компонент | Действие |
|-----------|----------|
| Notification sender | Очередь (Redis List/Stream) + worker с rate limit |
| Analytics job | Реже (6–12 ч) или в low-traffic часы |
| Health check | Лёгкий check без getMe при частых probe |

### 4.2 При 100k

| Компонент | Куда выносить |
|-----------|----------------|
| **Scheduler** | Отдельный Worker (процесс/контейнер) |
| **Notification queue** | Redis Streams или RabbitMQ |
| **Analytics** | Отдельный ETL/worker, read replica |
| **Webhook receiver** | Отдельный HTTP service для payments (если ещё не сделан) |
| **Bot** | Несколько инстансов за LB при webhook |

### 4.3 Не выносить

| Компонент | Причина |
|-----------|---------|
| Payment processing | В основном боте (или в worker), но не отдельный микросервис на старте |
| Admin dashboard | В боте, низкая нагрузка |
| FSM | Redis — общий бэкенд, не отдельный сервис |

---

## 5. Конкретные изменения в коде

### 5.1 Throttled NotificationSender (10k+)

```python
# app/services/throttled_notifier.py
# Очередь asyncio.Queue, worker с rate 25 msg/s
# notifier.send() -> queue.put(); worker забирает и шлёт с паузой
```

### 5.2 Chunked habit_reminders (10k+)

```python
# Вместо result.all() — stream по 500
# for offset in range(0, total, 500):
#     chunk = await session.execute(select(...).limit(500).offset(offset))
#     for row in chunk: ...
#     await asyncio.sleep(20)  # пауза между чанками
```

### 5.3 Sharded habit_reminders (100k)

```python
# 10 jobs: habit_reminders_shard_0..9
# WHERE (h.user_id % 10) = :shard
# Cron: shard_i запускается в :02 + i*2 минут (например 09:02, 09:04, ...)
```

### 5.4 Redis FSM (при 2+ инстансах)

```python
# app/fsm/storage.py
# if settings.redis_url:
#     storage = RedisStorage(redis.from_url(settings.redis_url))
# else:
#     storage = MemoryStorage()
```

### 5.5 DB pool по окружению

```python
# pool_size=10 if users < 10k else 20
# Или из env: DB_POOL_SIZE, DB_MAX_OVERFLOW
```

---

## 6. Чек-лист по этапам

### 1k
- [ ] Мониторинг (Sentry, алерты)
- [ ] Проверить индексы в БД
- [ ] Документировать текущие лимиты

### 10k
- [ ] ThrottledNotifier / OutgoingMessageQueue
- [ ] Chunked habit_reminders
- [ ] Увеличить DB pool
- [ ] Redis для FSM (если 2 инстанса)

### 100k
- [ ] Вынести scheduler в Worker
- [ ] Redis: FSM, throttling, очередь
- [ ] Sharded habit_reminders
- [ ] Webhook для бота
- [ ] Read replica для analytics
- [ ] Connection pooler (PgBouncer)
