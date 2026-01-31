# Admin Dashboard

## Доступ

- Только пользователи из `ADMIN_IDS` (comma-separated)
- Команда `/admin`

## Разделы

| Раздел | Содержимое |
|--------|------------|
| System | DB, Scheduler, Bot status |
| Users | Total, по tier, новые за 24h/7d, привычки |
| Subscriptions | Active, revenue, expiring 72h |
| Finance | Payments succeeded, sum, balances total |
| Analytics | New users 24h, 7d, 30d |
| Errors & Alerts | Последние critical/warning логи и алерты |

## Rate limit

- 20 запросов в минуту на админа (клики по кнопкам)

## Примеры сообщений

**System Status:**
```
System Status

🟢 DB: OK
🟢 Scheduler: OK
🟢 Bot: OK
```

**Users:**
```
Users

👥 Total: 150
· Trial: 80 | Free: 40 | Premium: 30
· New today: 5 | 7d: 22
📋 Habits: 320
```

**Finance:**
```
Finance

💳 Payments (succeeded): 45
💰 Sum: 12500.00
🏦 Balances total: 3200.00
```
