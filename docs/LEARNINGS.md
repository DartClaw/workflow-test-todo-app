# Project Learnings

<!-- Organize by topic. Entries should be brief (1-2 sentences).
     The bar: "Would a competent developer with code and git access still get bitten?"
     Actively maintain: merge overlapping entries, remove stale knowledge, split large sections. -->

## HTMX + FastAPI Patterns

<!-- Gotchas and idioms specific to returning HTML fragments from FastAPI routes. -->

- Todo list content delegates item rendering through `todos_list.html` to `todo_item.html`; verify the existing item partial before changing list-level templates for todo display behavior.
- HTML `input[type=date]` submits `YYYY-MM-DD`; keep route parsing aligned with `format_date_input()` rather than a datetime-local format.

## SQLAlchemy + SQLite

<!-- Pooling, threading, ordering, cascade quirks encountered while working with the DB layer. -->

- _(none yet)_

## Authentication (intentionally simplified)

<!-- The in-memory session dict + plain-text passwords are deliberate. Record non-obvious consequences. -->

- _(none yet)_

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
