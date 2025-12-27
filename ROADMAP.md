# Uptime Monitor — Roadmap


## Phase 1 — Stabilization (MVP+)

Цель: довести текущий функционал до надёжного состояния.

### Monitoring
- [ ] Фиксация начала и окончания инцидента (incident_id)
- [ ] Корректный подсчёт downtime как одного инцидента
- [ ] Защита от флаппинга (debounce: N проверок подряд)

### Data
- [ ] Таблица `incidents` (start_ts, end_ts, duration)
- [ ] Связь downtime_log → incident_id
- [ ] Очистка дублирующих status_history

### API
- [ ] `/api/incidents`
- [ ] `/api/site/<url>/history`

---

## Phase 2 — Alerting

Цель: сделать мониторинг практическим.

### Notifications
- [ ] Telegram notifications (offline / recovery)
- [ ] Rate limit на уведомления
- [ ] Настройки per-site

### SLA
- [ ] SLA target (99.9 / 99.5 / custom)
- [ ] SLA breach detection
- [ ] Отображение breach в UI

---

## Phase 3 — Configuration & Control

Цель: уйти от ручного редактирования JSON.

### Admin API
- [ ] Добавление / удаление сайтов через API
- [ ] Enable / disable site
- [ ] Изменение интервала проверки

### Security
- [ ] Admin token
- [ ] Read-only public mode

---

## Phase 4 — UX & Observability

Цель: удобство и аналитика.

### UI
- [ ] Страница сайта (drill-down)
- [ ] График uptime / downtime
- [ ] История инцидентов

### Export
- [ ] CSV export
- [ ] JSON API for integrations

---

## Phase 5 — Scalability (optional)

Цель: подготовка к росту.

- [ ] Отделение monitor в отдельный сервис
- [ ] Multiple workers
- [ ] PostgreSQL support
- [ ] Async checks (aiohttp)

---

## Non-goals

- Synthetic monitoring
- Browser checks
- Heavy dashboards
