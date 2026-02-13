# Architecture Audit — OnlyBot Production Recovery

**Date:** 2025-01-31  
**Mode:** Senior Staff / Principal Engineer  
**Status:** PRODUCTION BLOCKER — Full system restoration

---

## 1. Models

| Model | Table | Primary Key |
|-------|-------|-------------|
| User | users | id (BigInteger) |
| Habit | habits | id |
| HabitSchedule | habit_schedules | id |
| HabitLog | habit_logs | id |
| HabitDeclineNote | habit_decline_notes | id |
| Balance | balances | id |
| Payment | payments | id |
| BalanceTransaction | balance_transactions | id |
| Subscription | subscriptions | id |
| Referral | referrals | id |
| Achievement | achievements | id |
| UserAchievement | user_achievements | id |
| AnalyticsMetric | analytics_metrics | id |
| SystemLog | system_logs | id |
| AdminAlert | admin_alerts | id |

---

## 2. User Model Columns (ORM vs DB)

### ORM Columns (app/models/user.py)
| Column | Type | Nullable | Default | In 001 | In 004-007 |
|--------|------|----------|---------|--------|------------|
| id | BigInteger | NO | — | ✅ | — |
| telegram_id | BigInteger | NO | — | ✅ | — |
| username | String(255) | YES | — | ✅ | — |
| first_name | String(255) | NO | "" | ✅ | — |
| last_name | String(255) | YES | — | ✅ | — |
| language_code | String(10) | NO | "en" | ✅ | — |
| tier | String(20) | NO | UserTier.TRIAL | ✅ | — |
| trial_ends_at | DateTime(TZ) | YES | — | ✅ | — |
| timezone | String(50) | NO | "UTC" | ✅ | — |
| is_blocked | Boolean | NO | False | ✅ | — |
| referral_code | String(32) | YES | — | ✅ | — |
| referred_by_id | BigInteger | YES | — | ✅ | — |
| device_fingerprint | String(64) | YES | — | ✅ | — |
| created_at | DateTime(TZ) | NO | now() | ✅ | — |
| updated_at | DateTime(TZ) | NO | now() | ✅ | — |
| last_inactivity_reminder_at | DateTime(TZ) | YES | — | — | 007 |
| last_streak_milestone | Integer | YES | — | — | 007 |
| **notifications_enabled** | **Boolean** | **NO** | **True** | — | **004, 007** |
| last_profile_quote_index | Integer | YES | — | — | 004, 007 |
| last_insight_at | DateTime(TZ) | YES | — | — | 005, 007 |
| last_insight_id | Integer | YES | — | — | 005, 007 |
| profile_views_count | Integer | NO | 0 | — | 006, 007 |
| last_paywall_shown_at | DateTime(TZ) | YES | — | — | 006, 007 |

### Root Cause: UndefinedColumnError
- **ORM expects:** notifications_enabled
- **DB may lack:** if migrations 004–006 were not applied (e.g. fresh 001-only DB, partial deploy)
- **Fix:** Migration 007 is idempotent and adds all missing columns

---

## 3. Migrations

| Revision | Name | Adds |
|----------|------|------|
| 001 | initial_production_schema | users, habits, schedules, logs, balances, payments, subscriptions, referrals, system_logs, admin_alerts |
| 002 | analytics_metrics | analytics_metrics table |
| 003 | retention_autorenew | retention-related fields |
| 004 | profile_settings | notifications_enabled, last_profile_quote_index |
| 005 | insights | last_insight_at, last_insight_id |
| 006 | achievements_calendar_retention | achievements, user_achievements, profile_views_count, last_paywall_shown_at |
| 007 | users_sync_schema | idempotent add: last_inactivity_reminder_at, last_streak_milestone, notifications_enabled, last_profile_quote_index, last_insight_at, last_insight_id, profile_views_count, last_paywall_shown_at |

### Missing Migrations
- None. 007 covers schema drift from missed 004–006.

### Columns Used in Code but Not in DB (if 007 not applied)
- notifications_enabled → UndefinedColumnError
- profile_views_count, last_paywall_shown_at, last_insight_*, last_profile_quote_index, last_inactivity_reminder_at, last_streak_milestone

---

## 4. Entrypoints & Polling

| File | Entrypoint | Polling | Used By |
|------|------------|---------|---------|
| run.py | main_orchestrator.main | dp.run_polling(bot) | railway.json, Dockerfile, nixpacks.toml ✅ |
| app/main.py | app.main.main | dp.run_polling(bot) | NOT used — DEAD CODE ⚠️ |

**Risk:** Running `python -m app.main` would start a second bot instance → TelegramConflictError.

**Fix:** Deprecate/remove app/main.py or ensure only run.py is ever used.

---

## 5. Scheduler

- **Implementation:** app/scheduler/init.py → AsyncIOScheduler, in-memory JobStore
- **Jobs:** app/scheduler/jobs.py → setup_scheduler registers habit_reminders, trial_notifications, subscription_notifications, health_check
- **Single init:** app.core.scheduler re-exports from app.scheduler
- **SQLAlchemyJobStore:** Removed previously — required psycopg2 (sync), incompatible with async architecture. In-memory is acceptable for single Railway replica; jobs re-register on startup.

---

## 6. Middlewares

| Middleware | Purpose | Fail-Safe |
|------------|---------|-----------|
| FSMTimeoutMiddleware | FSM timeout | — |
| ThrottlingMiddleware | Rate limit | — |
| UserContextMiddleware | Inject user, session | ✅ Schema error → minimal user, continue pipeline |

---

## 7. Config / Settings

- **Source:** app/config/settings.py (Pydantic BaseSettings)
- **Import:** app.config.settings OR app.core.config (core re-exports)
- **Required:** BOT_TOKEN, DATABASE_URL
- **Optional:** ADMIN_IDS, ALERT_CHAT_ID, BOT_INSTANCE_ROLE

---

## 8. Railway / Deploy

| Config | Value |
|--------|-------|
| railway.json startCommand | python scripts/deploy_gate.py && python run.py |
| healthcheckPath | /health |
| healthcheckTimeout | 30 |
| restartPolicyType | ON_FAILURE |
| restartPolicyMaxRetries | 10 |

**Deploy gate:** alembic upgrade head + verify current == heads. Exit 1 on mismatch.

---

## 9. Risk Areas

1. **Duplicate app/main.py** — Can cause TelegramConflictError if run
2. **BOT_INSTANCE_ROLE** — If set and not "primary", bootstrap aborts; if unset, any instance runs (rely on Railway scale=1)
3. **Schema drift** — Mitigated by deploy_gate, bootstrap verify_schema, middleware fail-safe, scheduler circuit breaker
4. **In-memory scheduler** — Jobs lost on restart; re-registered on startup. Acceptable for single instance.

---

## 10. Dead / Duplicate Code

- app/main.py — Alternative entrypoint, outdated (missing routers, no bootstrap). Should be removed or deprecated.
- app.core.health, app.core.health_server — Re-exports from app.monitoring; fine.

---

## 11. Startup Order (Current)

1. run.py → main_orchestrator.main()
2. setup_logging
3. Check BOT_TOKEN
4. Create Bot, Dispatcher
5. Register middlewares, routers
6. on_startup: bootstrap → init_db → health_server → scheduler (if schema_ok)
7. dp.run_polling(bot)

**Bootstrap:** check_instance_role → check_migrations_pending → verify_schema

---

## 12. Recommendations (Implemented)

1. ✅ app/main.py redirects to main_orchestrator
2. ✅ validate_environment() for BOT_TOKEN
3. ✅ /health/deep endpoint
4. ✅ PostgreSQL advisory lock (pg_try_advisory_lock) for single-instance enforcement
5. Ensure Railway: replicas=1, BOT_INSTANCE_ROLE=primary
