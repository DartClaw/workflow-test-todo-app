# Project Learnings

<!-- Organize by topic. Entries should be brief (1-2 sentences).
     The bar: "Would a competent developer with code and git access still get bitten?"
     Actively maintain: merge overlapping entries, remove stale knowledge, split large sections. -->

## HTMX + FastAPI Patterns

<!-- Gotchas and idioms specific to returning HTML fragments from FastAPI routes. -->

- Return a count OOB partial alongside `swap: 'delete'` todo deletions to keep sidebar counters in sync, because HTMX can remove the row target even when response target is otherwise absent.

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

- Regression for OOB-delete behavior works best with route-response assertions (`hx-swap-oob`, list-id target) plus DB count checks in the same test, not browser-only checks.
