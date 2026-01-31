# Payments Module

## Архитектура

```
PaymentService (unified)
    ├── create_balance_topup()
    ├── create_subscription_payment()
    └── process_webhook()
         ├── verify (provider)
         ├── parse (provider)
         ├── idempotency check (provider + provider_payment_id)
         └── _complete_payment()
              ├── balance_topup → _credit_balance + BalanceTransaction
              └── subscription → _activate_subscription
```

## Провайдеры

| Provider | create_payment | webhook |
|----------|----------------|---------|
| YooKassa | redirect URL | HTTP POST |
| Telegram Stars | handler sendInvoice | successful_payment |
| CryptoBot | createInvoice API | HTTP POST |

## Idempotency

- **create:** idempotency_key — повторный вызов возвращает существующий payment
- **webhook:** provider + provider_payment_id — повторный webhook игнорируется

## Flow

### Balance top-up
1. `create_balance_topup(user_id, amount, provider)`
2. Payment (pending) + provider invoice
3. Webhook → `process_webhook` → credit balance, BalanceTransaction

### Subscription
1. `create_subscription_payment(user_id, plan_id, amount, provider)`
2. Webhook → create Subscription, User.tier=premium, User.trial_ends_at=null

## Scheduler

Trial/subscription jobs сканируют БД. При активации подписки:
- User.tier=premium, trial_ends_at=null → trial job пропускает пользователя
- Новая Subscription → subscription_expiry job подхватывает автоматически

Дополнительных действий со scheduler не требуется.

## Защита от дублей

| Уровень | Механизм |
|---------|----------|
| create | idempotency_key — повторный вызов с тем же key возвращает существующий payment |
| webhook | provider + provider_payment_id — уже обработанный платёж пропускается |
| DB | unique(idempotency_key), index(provider, provider_payment_id) |
