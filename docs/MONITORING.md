# Monitoring & Admin Alerts

## Health Checks

| Component | Check |
|-----------|-------|
| bot | getMe() |
| database | SELECT 1 |
| scheduler | scheduler.running |

## Error Classification

| Severity | Cooldown | Example |
|----------|----------|---------|
| critical | 5 min | Database down, bot unreachable |
| warning | 15 min | Scheduler stopped |

## Deduplication

- **error_hash:** `sha256(severity:source:message)[:32]` или явный fingerprint
- **cooldown:** не слать повторный alert с тем же fingerprint в течение интервала
- **AdminAlert** — все отправленные алерты пишутся в БД

## Recovery

Когда компонент, который был down, снова ok — отправляется `[RECOVERED]`.

## Примеры алертов

```python
from app.monitoring.admin_alert_service import AdminAlertService
from app.config.constants import AlertSeverity

# Critical — payment webhook verification failed
alert_svc = AdminAlertService(bot)
await alert_svc.send_alert(
    AlertSeverity.CRITICAL,
    source="payment_webhook",
    message="YooKassa callback verification failed",
    details={"provider": "yookassa"},
)

# Warning — high error rate
await alert_svc.send_alert(
    AlertSeverity.WARNING,
    source="scheduler",
    message="habit_reminders: 5 send failures in last run",
)
```

## DB Logging

`MonitoringService.log_to_db()` — все health результаты пишутся в `system_logs`.
