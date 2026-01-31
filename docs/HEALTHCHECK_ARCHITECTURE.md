# Архитектура запуска и Healthcheck (Railway)

## Проблема

Railway ожидает **HTTP endpoint** для healthcheck, а Telegram-бот — **long-polling приложение** без встроенного HTTP. Railway шлёт `GET /health` на порт `$PORT` до 300 секунд; если не получает 200 OK — деплой считается failed.

## Схема запуска

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         main() — точка входа                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  dp.run_polling(bot)  — aiogram создаёт event loop и запускает polling   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  on_startup(bot)  — колбэк aiogram (в том же event loop)                 │
│                                                                          │
│  1. Health server startup  ◄── ПЕРВЫМ: слушаем $PORT для Railway         │
│     • aiohttp web.Application                                            │
│     • GET /health → 503 до готовности, 200 когда всё ОК                  │
│     • Railway начинает проверять /health сразу после bind                 │
│                                                                          │
│  2. init_db() — PostgreSQL, создание таблиц                              │
│                                                                          │
│  3. setup_scheduler(bot) — APScheduler для напоминаний                   │
│                                                                          │
│  ► Все компоненты готовы → health возвращает 200                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Long polling  — бот обрабатывает updates                                │
│  Health server — продолжает отвечать на /health в том же event loop      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Важно для Railway

| Аспект | Решение |
|--------|---------|
| **Порт** | Слушаем `$PORT` (Railway), fallback `8080` локально |
| **Event loop** | Health server и бот — один процесс, один event loop |
| **Порядок старта** | Health server первым в on_startup, чтобы bind был до init_db |
| **200 vs 503** | 200 — bot OK + db OK + scheduler OK; 503 — хотя бы один failed |
| **Блокировки** | aiohttp async, не блокирует event loop |

## Таймлайн healthcheck

```
t=0s    Railway поднимает контейнер
t=1s    python run.py → run_polling
t=2s    on_startup → health server bind 0.0.0.0:$PORT
t=3s    Railway: GET /health → 503 (db/scheduler ещё не готовы)
t=5s    init_db done, setup_scheduler done
t=6s    Railway: GET /health → 200 OK ✓
t=6s+   Деплой помечен как успешный
```
