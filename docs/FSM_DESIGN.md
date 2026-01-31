# FSM Design — States & Transitions

## 0. States → Transitions (сводка)

| From State | Event | To State / Action |
|------------|-------|-------------------|
| — | /start | clear |
| — | /cancel | clear |
| choosing_template | habit_tpl:custom | waiting_name |
| choosing_template | habit_tpl:{id} | choosing_days |
| waiting_name | text (valid) | choosing_days |
| choosing_days | habit_day:{n} | choosing_days (toggle) |
| choosing_days | habit_days_ok | choosing_time |
| choosing_time | habit_time:{t} | choosing_time (toggle) |
| choosing_time | habit_time_ok | confirming |
| confirming | habit_confirm:yes | create + clear |
| confirming | habit_confirm:no | clear |
| adding_note (Decline) | text / preset / skip | log + clear |

---

## 1. StateGroup'ы

| Group | Сценарий |
|-------|----------|
| HabitCreateFSM | Создание привычки (шаблон/своя, дни, время, подтверждение) |
| HabitDeclineFSM | Отклонение с комментарием |
| SubscriptionFSM | Покупка подписки |
| BalanceFSM | Пополнение баланса |
| SettingsFSM | Настройки (timezone) |
| AdminFSM | Админ-панель |

---

## 2. HabitCreateFSM — создание привычки

| State | Назначение | Переход в |
|-------|------------|-----------|
| choosing_template | Шаблон или своя | waiting_name / applying_template |
| waiting_name | Ввод названия (если своя) | choosing_days |
| applying_template | Применение шаблона (name уже есть) | choosing_days |
| choosing_days | Multi-select дней недели | choosing_time |
| choosing_time | Multi-select времени | confirming |
| confirming | Подтверждение | — (create) / choosing_template (back) |

**FSM data:** `template_id`, `name`, `emoji`, `days` (list), `times` (list)

**Transitions:**
```
choosing_template --[template]--> applying_template --[next]--> choosing_days
choosing_template --[custom]--> waiting_name --[text]--> choosing_days
choosing_days --[callback]--> choosing_days (toggle)
choosing_days --[confirm]--> choosing_time
choosing_time --[callback]--> choosing_time (toggle)
choosing_time --[confirm]--> confirming
confirming --[confirm]--> [create] clear
confirming --[back]--> choosing_template
[any] --[/cancel]--> clear
[any] --[timeout]--> clear
```

---

## 3. HabitDeclineFSM — отклонение с комментарием

| State | Назначение | Переход в |
|-------|------------|-----------|
| choosing_habit | Выбор привычки для пропуска | adding_note |
| adding_note | Текст или preset | — (log) |

**FSM data:** `habit_id`

**Transitions:**
```
[handler habit_skip] --> adding_note
adding_note --[text]--> [log] clear
adding_note --[preset]--> [log] clear
adding_note --[/skip]--> [log] clear
[any] --[/cancel]--> clear
```

---

## 4. SubscriptionFSM — покупка подписки

| State | Назначение | Переход в |
|-------|------------|-----------|
| choosing_plan | Выбор тарифа | choosing_payment |
| choosing_payment | Выбор способа оплаты | processing |
| processing | Ожидание webhook / payment | — (done) |

**FSM data:** `plan_id`, `payment_provider`, `amount`

---

## 5. BalanceFSM — пополнение баланса

| State | Назначение | Переход в |
|-------|------------|-----------|
| choosing_amount | Выбор суммы | choosing_provider |
| choosing_provider | Выбор провайдера | processing |
| processing | Ожидание webhook | — (done) |

**FSM data:** `amount`, `provider`

---

## 6. Защита FSM

| Механизм | Реализация |
|----------|------------|
| Timeout | Middleware: state.clear() при отсутствии активности > N мин |
| Cancel | /cancel в любом state → clear + "Отменено" |
| Double-click | await callback.answer() в начале handler |
| Stale states | state.clear() при /start |
| Step jumping | Handlers привязаны к конкретным states |

---

## 7. Handlers по ответственности

| Handler | FSM | Действие |
|---------|-----|----------|
| add_habit_start, habit_new_cb | HabitCreateFSM | Set choosing_template |
| habit_template_cb | HabitCreateFSM | template → choosing_days; custom → waiting_name |
| habit_name_entered | HabitCreateFSM | Save name → choosing_days |
| habit_day_toggle_cb | HabitCreateFSM | Toggle day (остаёмся в choosing_days) |
| habit_days_confirm_cb | HabitCreateFSM | → choosing_time |
| habit_time_toggle_cb | HabitCreateFSM | Toggle time (остаёмся в choosing_time) |
| habit_time_confirm_cb | HabitCreateFSM | → confirming |
| habit_confirm_cb | HabitCreateFSM | Create via HabitService, clear |
| habit_skip_cb | HabitDeclineFSM | Set adding_note |
| habit_decline_preset_cb | HabitDeclineFSM | Log via service, clear |
| habit_decline_skip, habit_decline_with_text | HabitDeclineFSM | Log via service, clear |
| balance_topup_start | BalanceFSM | Set choosing_amount (skeleton) |
| cmd_cancel | Any | state.clear() |
| cmd_start | Any | state.clear() (reset) |

## 8. Файлы реализации

| Файл | Содержимое |
|------|------------|
| app/fsm/states.py | StateGroup'ы |
| app/fsm/context_data.py | Ключи FSM data |
| app/fsm/constants.py | Шаблоны, слоты времени, пресеты |
| app/middlewares/fsm_middleware.py | FSMTimeoutMiddleware |
| app/handlers/fsm_common.py | /cancel |
| app/handlers/habits.py | Habit create + decline |
| app/handlers/payments.py | Subscription + Balance (skeleton) |
| app/keyboards/fsm_habits.py | Template, days, time, confirm, decline presets |
