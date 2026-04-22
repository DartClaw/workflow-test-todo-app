# Ubiquitous Language

> Domain glossary for the todo-app. Canonical terms for use in code, documentation, and team communication.
>
> **Usage**: Use these exact terms in code (class names, variables, functions), documentation, and discussion. Avoid synonyms listed in the "Avoid" column.

## Todo Domain

| Term       | Definition                                                            | Avoid (synonyms)          | Bounded Context |
|------------|-----------------------------------------------------------------------|---------------------------|-----------------|
| User       | Authenticated account that owns todo lists                            | account, member           | Auth, Todo      |
| TodoList   | A named, ordered collection of todos belonging to one user            | list, collection, board   | Todo            |
| Todo       | A single task inside a TodoList                                       | task, item, entry         | Todo            |
| Position   | Integer defining display order within a parent collection             | index, rank, sort-order   | Todo            |
| Priority   | Importance level of a todo: `low` \| `medium` \| `high`               | severity, urgency         | Todo            |
| Due Date   | Date a todo is expected to be completed (stored naive)                | deadline, target date     | Todo            |
| Completion | State + timestamp indicating a todo has been finished                 | done, finished            | Todo            |
| Session    | Short-lived in-memory auth token mapped to a user                     | login, cookie, token      | Auth            |

## UI / HTMX Concepts

| Term             | Definition                                                                       | Avoid (synonyms)         | Bounded Context |
|------------------|----------------------------------------------------------------------------------|--------------------------|-----------------|
| Partial          | A server-rendered HTML fragment returned by a route                               | snippet, chunk           | Web             |
| OOB Swap         | Out-of-Band HTMX swap — updates a region outside the main target in one response  | side-update, secondary update | Web        |
| Error Partial    | `partials/error.html` rendered with an `{"error": "..."}` context                 | error JSON, error response (explicitly not JSON) | Web |

## Overloaded Terms

| Term    | Context A | Meaning A                     | Context B | Meaning B                                    |
|---------|-----------|-------------------------------|-----------|----------------------------------------------|
| `list`  | Code      | Python built-in `list` type   | Domain    | A `TodoList` entity — prefer `todo_list` / `TodoList` |

## Changelog

- 2026-04-22: Initial extraction during AndThen workflow init.
