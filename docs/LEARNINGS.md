# Project Learnings

<!-- Organize by topic. Entries should be brief (1-2 sentences).
     The bar: "Would a competent developer with code and git access still get bitten?"
     Actively maintain: merge overlapping entries, remove stale knowledge, split large sections. -->

## HTMX + FastAPI Patterns

<!-- Gotchas and idioms specific to returning HTML fragments from FastAPI routes. -->

- **HTMX route OC test coverage:** When an acceptance scenario says 'rendered list shows X', assert the HTML response content (e.g. `data-todo-priority="low"` and badge text) — not only the DB value. DB assertions (OC1) and rendering assertions (OC2) are independent failure modes in HTMX apps.

## SQLAlchemy + SQLite

<!-- Pooling, threading, ordering, cascade quirks encountered while working with the DB layer. -->

- _(none yet)_

## Authentication (intentionally simplified)

<!-- The in-memory session dict + plain-text passwords are deliberate. Record non-obvious consequences. -->

- _(none yet)_

## Jinja2 Templates

<!-- Gotchas and idioms specific to Jinja2 template rendering, nullable fields, and OOB partials. -->

- **Jinja2 partial defensive guard:** When adding a `{% set x = val or default %}` fallback for a nullable ORM field in a template, grep for all other uses of the raw `{{ model.field }}` in the same file — they need the same treatment. One-off `{% set %}` inside a conditional block leaves sibling attribute and onclick expressions still rendering `None`.

## Error Patterns

<!-- Log recurring errors. Deterministic errors (bad schema, wrong type) → conclude immediately.
     Infrastructure errors (timeout, rate limit) → log, no conclusion until pattern emerges.
     Conclusions graduate into the relevant topic section above. -->

| Error | Type | Conclusion |
|-------|------|------------|
| _(none yet)_ | | |

## Process & Tooling

<!-- Non-code knowledge: test prerequisites, agent workflow patterns, CI quirks. -->

- _(none yet)_
