# Team Guide — HabitBot

Руководство для инженерной команды. CTO-level view на архитектуру, onboarding, стандарты и процесс разработки.

---

## 1. Архитектура проекта

### 1.1 Обзор

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ENTRY POINT                                  │
│  run.py → main_orchestrator → Bot, Dispatcher, on_startup/shutdown   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│ Health Server │          │   Polling     │          │   Scheduler   │
│ aiohttp :PORT │          │   aiogram     │          │ APScheduler   │
│ GET /health   │          │   handlers    │          │ PostgreSQL    │
└───────────────┘          └───────────────┘          └───────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  PostgreSQL   │          │   Services    │          │   Payments    │
│  SQLAlchemy   │          │  (domain)     │          │ YooKassa, etc │
│  AsyncPG      │          │  Repositories │          │ Webhooks      │
└───────────────┘          └───────────────┘          └───────────────┘
```

### 1.2 Слои и ответственность

| Слой | Директория | Назначение |
|------|------------|------------|
| **Core** | `app/core/` | Конфиг, логирование, health checks, scheduler init |
| **Models** | `app/models/` | SQLAlchemy модели, init_db |
| **Repositories** | `app/repositories/` | Data access: CRUD без бизнес-логики |
| **Services** | `app/services/` | Бизнес-логика: привычки, платежи, рефералы, retention |
| **Integrations** | `app/integrations/` | PaymentService, провайдеры, webhook_processor |
| **Handlers** | `app/handlers/` | aiogram: команды, callbacks, тонкий слой |
| **FSM** | `app/fsm/` | Состояния, storage (Memory/Redis), context data |
| **Keyboards** | `app/keyboards/` | InlineKeyboard, ReplyKeyboard |
| **Middlewares** | `app/middlewares/` | Throttle, UserContext, FSM timeout |
| **Admin** | `app/admin/` | Роутер админ-панели |
| **Monitoring** | `app/monitoring/` | AdminAlertService, health aggregation |
| **Texts** | `app/texts/` | Централизованные строки UI |
| **Utils** | `app/utils/` | Retry, timezone, validators |

### 1.3 Поток зависимостей (без circular imports)

```
core
  ↑
infrastructure (models, db)
  ↑
repositories
  ↑
services (domain logic)
  ↑
integrations (payments)
  ↑
handlers, admin, scheduler
```

### 1.4 Ключевые документы

| Документ | Содержание |
|----------|------------|
| `docs/CLEAN_ARCHITECTURE.md` | Слои, роли, dependency flow |
| `docs/DATABASE_SCHEMA.md` | Модели, связи |
| `docs/FSM_DESIGN.md` | States, transitions |
| `docs/PAYMENTS.md` | PaymentService, idempotency |
| `docs/SCHEDULER.md` | Jobs, JobStore |
| `docs/MONITORING.md` | Health, alerts |
| `docs/OPERATIONAL_PLAYBOOK.md` | Инциденты, recovery |
| `docs/SCALING_ARCHITECTURE.md` | Bottlenecks, scaling |

---

## 2. Onboarding для разработчиков

### 2.1 Первый день

1. **Клонировать репозиторий**
   ```bash
   git clone <repo>
   cd OnlyBot
   ```

2. **Окружение**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Конфигурация**
   ```bash
   cp .env.example .env
   # Заполнить BOT_TOKEN, DATABASE_URL (локальный PostgreSQL или Railway)
   # ADMIN_IDS — свой Telegram ID для доступа к /admin
   ```

4. **База данных**
   ```bash
   # Локально: создать БД и запустить миграции
   createdb habitbot
   alembic upgrade head
   ```

5. **Запуск**
   ```bash
   python run.py
   ```

6. **Проверка**
   - Открыть бота в Telegram, отправить /start
   - Открыть /admin (если ID в ADMIN_IDS)
   - `curl http://localhost:8080/health` → 200

### 2.2 Неделя 1 — Ориентация

| День | Задача |
|------|--------|
| 1 | Окружение, запуск, прочитать README и ARCHITECTURE.md |
| 2 | Изучить flow: handler → service → repository; FSM states |
| 3 | Добавить простой handler (например, /help) и пройти code review |
| 4 | Разобрать один полный сценарий (создание привычки или платёж) |
| 5 | Прочитать OPERATIONAL_PLAYBOOK, разобрать monitoring |

### 2.3 Полезные команды

```bash
# Линтер / форматирование
ruff check app/
ruff format app/

# Миграции
alembic revision -m "add_feature_x"
alembic upgrade head

# Тесты (когда добавлены)
pytest
pytest -v tests/unit/
```

### 2.4 Контакты и каналы

- **Технические вопросы:** issue в репозитории или внутренний чат
- **Инциденты:** см. OPERATIONAL_PLAYBOOK.md
- **Архитектурные решения:** обсуждение в PR или ADR

---

## 3. Coding Rules

### 3.1 Общие принципы

1. **Handlers — тонкий слой.** Парсинг → вызов service → ответ. Бизнес-логика только в services.
2. **Тексты в app/texts.** Не хардкодить строки в handlers.
3. **Type hints везде.** Функции, аргументы, возвращаемые значения.
4. **Async/await.** Все I/O — асинхронно. Sync-код в `asyncio.to_thread` при необходимости.
5. **Timezone-aware.** `datetime.now(timezone.utc)` или `zoneinfo.ZoneInfo(user_tz)`.

### 3.2 Стиль кода

- **Ruff:** `ruff check`, `ruff format`. Настройки в `pyproject.toml`.
- **Длина строки:** 100 символов.
- **Imports:** stdlib → third-party → app, пустая строка между группами.
- **Docstrings:** для публичных функций и классов.

### 3.3 Слои и импорты

| Откуда | Можно импортировать |
|--------|---------------------|
| handlers | services, repositories (через DI), keyboards, texts, fsm |
| services | repositories, models, integrations |
| repositories | models, db session |
| integrations | models, config |

**Запрещено:** handlers → models напрямую (через services); services → handlers; circular imports.

### 3.4 Работа с БД

- **Session:** `async with session_factory() as session:` — всегда через context manager.
- **Миграции:** любые изменения схемы — через Alembic, не через `create_all`.
- **Транзакции:** `session.commit()` в конце use case; при ошибке — rollback автоматически.

### 3.5 Платежи

- **Idempotency:** всегда использовать `idempotency_key` при create; проверять `provider_payment_id` в webhook.
- **Логировать:** успешные и неуспешные операции, без секретов.

### 3.6 FSM

- **States:** определять в `app/fsm/states.py`.
- **Context data:** типизированные ключи в `app/fsm/context_data.py`.
- **Reset:** /cancel и /start сбрасывают FSM. Не оставлять пользователя «зависшим».

### 3.7 Обработка ошибок

- Логировать с `logger.exception` при неожиданных ошибках.
- Пользователю — короткое сообщение из `app/texts` (ERROR_GENERIC и т.д.).
- Критичные ошибки — AdminAlertService.

### 3.8 Тесты (рекомендации)

- **Unit:** services, repositories — мокировать session, внешние API.
- **Integration:** handler + service + test DB (опционально).
- Не коммитить падающие тесты.

---

## 4. Release Flow

### 4.1 Ветки

| Ветка | Назначение |
|-------|------------|
| `main` | Production. Всегда стабильна. |
| `develop` | Интеграционная ветка (опционально). |
| `feature/*`, `fix/*` | Ветки от main (или develop). |

### 4.2 Процесс разработки

1. Создать ветку от `main`: `git checkout -b feature/habit-export`
2. Коммиты: осмысленные сообщения, `fix:`, `feat:`, `docs:`, `refactor:`.
3. Push и открыть Pull Request.
4. Code review — минимум один апрув.
5. CI (если настроен): lint, tests.
6. Merge в `main`.

### 4.3 Перед релизом

Чек-лист (см. `docs/PRE_RELEASE_CHECKLIST.md`):

```
[ ] alembic upgrade head (миграции применены)
[ ] ALERT_CHAT_ID, ADMIN_IDS заданы в prod
[ ] Webhook URL настроен (YooKassa, CryptoBot)
[ ] SENTRY_DSN (рекомендуется)
[ ] Тест платежа в sandbox
[ ] curl /health → 200
```

### 4.4 Деплой

- **Railway:** push в `main` → автоматический деплой (если настроен).
- **Ручной:** `railway up` или `docker build` + `docker run`.
- **Миграции:** выполняются в deploy step или в `on_startup` (осторожно при нескольких инстансах).

### 4.5 Версионирование

- `pyproject.toml` — `version = "0.1.0"`.
- Семантическое версионирование: `MAJOR.MINOR.PATCH`.
- Тег при релизе: `git tag v0.1.1 && git push origin v0.1.1`.

### 4.6 Rollback

- Railway: откат на предыдущий deploy.
- БД: миграции вниз (`alembic downgrade -1`) только при обратимых миграциях.
- При сомнениях — восстановить из бэкапа, см. OPERATIONAL_PLAYBOOK.

---

## 5. Product Roadmap

### 5.1 Текущее состояние (v0.1)

- ✅ Привычки: создание, расписание, логирование, decline
- ✅ Trial / Free / Premium тарифы
- ✅ Платежи: YooKassa, CryptoBot, Telegram Stars
- ✅ Баланс, автопродление подписки
- ✅ Рефералы, антифрод
- ✅ Scheduler: reminders, trial/subscription уведомления
- ✅ Retention: inactivity reminders, streak rewards
- ✅ Admin dashboard, мониторинг, алерты

### 5.2 Ближайшие приоритеты (Q1)

| # | Фича | Описание | Приоритет |
|---|------|----------|-----------|
| 1 | Webhook endpoint | POST /webhook/yookassa, /webhook/cryptobot для приёма платежей | P0 |
| 2 | Redis FSM | Замена MemoryStorage для масштабирования | P1 |
| 3 | Sentry | Интеграция для ошибок в prod | P1 |
| 4 | Rate limit feedback | Сообщение «Слишком много запросов» вместо молчаливого skip | P2 |
| 5 | Export привычек | Выгрузка в CSV/PDF для Premium | P2 |

### 5.3 Средний горизонт (Q2)

| # | Фича | Описание |
|---|------|----------|
| 1 | Gamification | Бейджи, достижения, лидерборды |
| 2 | Групповые привычки | Челленджи с друзьями |
| 3 | Интеграции | Календарь, Notion (webhook) |
| 4 | A/B тесты | Разные онбординги, ценовые предложения |
| 5 | Локализация | EN, RU, другие языки |

### 5.4 Долгосрочно (Q3–Q4)

| # | Направление | Описание |
|---|-------------|----------|
| 1 | Масштабирование | Redis rate limit, sharded scheduler, webhook mode |
| 2 | Аналитика | Расширенные метрики, воронки, когорты |
| 3 | B2B | Корпоративные подписки, white-label |
| 4 | Mobile companion | PWA или нативное приложение |
| 5 | AI-подсказки | Персонализированные рекомендации по привычкам |

### 5.5 Критерии приоритизации

- **P0:** Блокирует работу продукта (платежи, доступ).
- **P1:** Существенно улучшает стабильность или UX.
- **P2:** Желательно, не блокер.
- Roadmap пересматривается ежемесячно.

---

## 6. Быстрые ссылки

| Ресурс | Путь |
|--------|------|
| Entry point | `run.py` → `app/main_orchestrator.py` |
| Handlers | `app/handlers/` |
| Services | `app/services/` |
| Repositories | `app/repositories/` |
| Models | `app/models/` |
| Тексты | `app/texts/__init__.py` |
| FSM states | `app/fsm/states.py` |
| Scheduler jobs | `app/scheduler/jobs.py`, `job_runner.py` |
| Admin | `app/admin/router.py` |
