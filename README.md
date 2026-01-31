# HabitBot — Telegram-бот для отслеживания привычек

Production-ready бот на Python 3.12, aiogram 3.x, PostgreSQL.

## Railway Healthcheck

Бот запускает минимальный HTTP‑сервер (aiohttp) в том же event loop, что и polling. Endpoint `GET /health` проверяет:

- **bot** — доступность Telegram API (getMe)
- **database** — подключение к PostgreSQL
- **scheduler** — статус APScheduler

Возвращает **200 OK** если всё готово, **503** при сбое. Railway использует переменную `PORT` — сервер слушает её автоматически.

## Быстрый старт

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # BOT_TOKEN, DATABASE_URL, ADMIN_IDS
python run.py
```

## Деплой на Railway

1. Подключите репозиторий, добавьте PostgreSQL
2. Переменные: `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_IDS`
3. Railway задаёт `PORT` и проверяет `/health` — настраивать не нужно

## Для команды

Полное руководство для разработчиков: **[docs/TEAM_GUIDE.md](docs/TEAM_GUIDE.md)**

- Архитектура проекта
- Onboarding
- Coding rules
- Release flow
- Product roadmap
