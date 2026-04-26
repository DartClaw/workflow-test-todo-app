# Product Backlog

## Validated

<!-- Requirements confirmed and accepted for implementation. -->

| REQ-ID  | Description | Priority | Stories | Status    |
|---------|-------------|----------|---------|-----------|
| _(none yet)_ | | | | |

## Active (Under Discussion)

<!-- Requirements being refined or awaiting validation. -->

| REQ-ID  | Description | Priority | Open Questions |
|---------|-------------|----------|----------------|
| _(none yet)_ | | | |

## Known Defects

<!-- Reported bugs awaiting triage or fix. Reference by BUG-ID in stories and PRs. -->

| BUG-ID  | Description | Severity | Stories | Status |
|---------|-------------|----------|---------|--------|
| BUG-001 | Sidebar incomplete-count does not update when a todo is deleted; it only refreshes on full page reload. Toggling completion updates the count correctly, so the expected pattern is an HTMX out-of-band swap on the delete response. | High | — | Open |
| BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open |
| BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |
| BUG-004 | Overdue and "due today" styling apply to the wrong todos. Todos due today render as overdue (red), and "due today" (amber) styling never appears. Root cause is comparing full datetimes instead of calendar dates. | Medium | — | Open |

## Out of Scope

<!-- Explicitly excluded requirements – useful to prevent scope creep. -->

- **Production-grade authentication** — plain-text passwords and in-memory sessions are deliberate educational simplifications.
- **Persistent session store** — sessions are expected to vanish on restart.
