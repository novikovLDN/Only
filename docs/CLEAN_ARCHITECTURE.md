# Clean Architecture — Telegram Bot (aiogram 3.x)

## Entrypoint

Использовать оркестратор:

```bash
python -c "from app.main_orchestrator import main; main()"
```

Или обновить `run.py`:

```python
from app.main_orchestrator import main
main()
```

---

## 1. Структура директорий

```
app/
├── __init__.py
├── main.py                         # Entrypoint-оркестратор
│
├── core/                           # Ядро: конфиг, логирование, health, scheduler
│   ├── __init__.py
│   ├── config.py                   # Settings, constants
│   ├── logging.py                  # Настройка логгера
│   ├── health.py                   # Проверки: db, scheduler, bot
│   ├── health_server.py            # aiohttp GET /health
│   └── scheduler.py                # APScheduler setup
│
├── bot/                            # Presentation: handlers, FSM, UI
│   ├── __init__.py
│   ├── router.py                   # Агрегация роутеров
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py
│   │   ├── habits.py
│   │   └── ...
│   ├── fsm/
│   │   ├── __init__.py
│   │   ├── states.py
│   │   └── storage.py
│   ├── keyboards/
│   │   └── __init__.py
│   └── middlewares/
│       └── __init__.py
│
├── domain/                         # Бизнес-логика (use cases)
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── user.py
│       ├── habit.py
│       └── ...
│
├── infrastructure/                 # Внешние системы: DB, платежи, уведомления
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py              # Async session, engine
│   │   ├── models/                 # SQLAlchemy models
│   │   └── repositories/           # Data access
│   ├── payments/
│   │   ├── __init__.py
│   │   └── ...
│   └── notifications/
│       └── __init__.py
│
└── admin/                          # Админка: dashboard, метрики, алерты
    ├── __init__.py
    ├── router.py
    ├── handlers.py
    ├── metrics.py
    └── alerting.py
```

---

## 2. Роли слоёв

### core — ядро (без зависимостей от домена/инфраструктуры)

- **config** — переменные окружения, константы. Единая точка конфигурации.
- **logging** — настройка structlog/logging, форматы.
- **health** — проверки доступности db, scheduler, bot. Используется health_server.
- **health_server** — минимальный aiohttp сервер для Railway.
- **scheduler** — инициализация APScheduler, регистрация cron/interval jobs.

**Импорты:** только stdlib и внешние пакеты (pydantic, aiohttp). Никаких `app.domain`, `app.infrastructure`.

---

### bot — presentation (aiogram)

- **handlers** — обработка команд, сообщений, callback. Тонкий слой: парсинг → вызов domain-сервиса → ответ.
- **fsm** — состояния FSM, storage (Redis/Memory).
- **keyboards** — InlineKeyboard, ReplyKeyboard.
- **middlewares** — throttle, user context, logging.

**Импорты:** `domain`, `infrastructure` (для DI), `core`.

---

### domain — бизнес-логика

- **services** — use cases: создание привычки, логирование, рефералы, платежи. Без знания aiogram.

**Импорты:** `infrastructure` (repositories, абстракции), `core`. Никаких `bot`, `aiogram`.

---

### infrastructure — реализации внешних систем

- **db** — SQLAlchemy models, repositories, session factory.
- **payments** — провайдеры (YooKassa, Stars), payment service.
- **notifications** — отправка сообщений в Telegram (обёртка над Bot).

**Импорты:** `core`. Никаких `domain` в моделях — только в repositories (через session).

---

### admin — админка

- **handlers** — /admin, /admin_logs, broadcast.
- **metrics** — агрегация для дашборда.
- **alerting** — отправка алертов в Telegram при ошибках.

**Импорты:** `domain`, `infrastructure`, `core`, `bot` (router).

---

## 3. Dependency flow (защита от circular imports)

```
core          ← (никаких app-зависимостей)
  ↑
infrastructure
  ↑
domain
  ↑
bot ────────→ admin
```

- **core** — корень, импортируется всеми.
- **infrastructure** — импортирует только core.
- **domain** — импортирует infrastructure, core.
- **bot** — импортирует domain, infrastructure, core.
- **admin** — импортирует domain, infrastructure, core, bot (только router).

---

## 4. main.py как оркестратор

- Создаёт Bot, Dispatcher.
- Регистрирует middlewares.
- Подключает роутеры (bot + admin).
- В `on_startup`: health server → init_db → scheduler.
- В `on_shutdown`: health server cleanup → scheduler shutdown → db close.
- Запускает `run_polling`.

main.py не содержит бизнес-логики, только сборку и lifecycle.

---

## 5. Масштабируемость

| Аспект | Решение |
|--------|---------|
| Новый handler | Добавить в `bot/handlers/`, зарегистрировать в `bot/router.py` |
| Новый сервис | Добавить в `domain/services/` |
| Новая таблица | `infrastructure/db/models/` + repository |
| Новый платёжный провайдер | `infrastructure/payments/` |
| Redis FSM | Заменить storage в `bot/fsm/` |
| Мультиинстанс | Redis scheduler (Celery Beat) вместо APScheduler |

---

## 6. Поддержка

- Слои изолированы — можно тестировать domain без aiogram.
- Миграция: перемещение файлов без изменения контрактов.
- Новые разработчики: чёткое место для каждой сущности.
