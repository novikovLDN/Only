<<<<<<< HEAD
# HabitBot — Telegram-бот для отслеживания привычек

Production-ready бот на Python 3.12, aiogram 3.x, PostgreSQL.

## Возможности

- Создание и отслеживание привычек
- Напоминания по расписанию (timezone-aware)
- Trial / Free / Premium тарифы
- Реферальная система с антифродом
- Платежи: ЮКасса, Telegram Stars, CryptoBot
- Внутренний баланс
- Админ-панель
- Health checks для Railway

## Быстрый старт

```bash
# Виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows

# Зависимости
pip install -r requirements.txt

# Переменные окружения
cp .env.example .env
# Отредактируйте .env: BOT_TOKEN, DATABASE_URL, ADMIN_IDS

# Запуск
python run.py
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| BOT_TOKEN | Токен бота от @BotFather |
| DATABASE_URL | PostgreSQL (postgresql+asyncpg://...) |
| ADMIN_IDS | ID админов через запятую |
| ALERT_CHAT_ID | ID чата для алертов |
| YOOKASSA_* | ЮКасса (опционально) |
| CRYPTOBOT_TOKEN | CryptoBot (опционально) |

## Миграции

```bash
# Создать миграцию
alembic revision --autogenerate -m "description"

# Применить
alembic upgrade head
```

## Деплой на Railway

1. Подключите репозиторий
2. Добавьте PostgreSQL
3. Установите переменные окружения
4. Health check: `/health` на порту 8080

## Структура

```
app/
├── config/       # Настройки
├── models/       # SQLAlchemy модели
├── repositories/ # Доступ к данным
├── services/     # Бизнес-логика
├── handlers/     # aiogram обработчики
├── fsm/          # FSM состояния
├── integrations/ # Платежи
├── scheduler/    # Напоминания
├── monitoring/   # Health, алерты
└── middlewares/  # Rate limit, user context
```

## Риски и ограничения

- **Redis для FSM**: при масштабировании замените MemoryStorage на RedisStorage
- **Scheduler**: один инстанс; для нескольких — Celery Beat или аналоги
- **Idempotency**: все платежные webhook проверяют idempotency_key
=======
# Only
>>>>>>> 6f004eca89a26213ac2df16f3511f3c7246271b2
