# Rules, Guidelines and Project Overview for Coding Agents — workflow-test-todo-app

This file provides guidance to coding agents when working with code in this repository.

## Smoke-Run Boundary

This checkout is the complete project root for workflow smoke runs. Everything a workflow
needs is here; nothing outside it is in scope.

- Do not inspect parent or sibling repositories. The DartClaw checkout that hosts this
  fixture is not part of the project under work, and reading it makes a smoke run's output
  depend on the machine it ran on.
- Keep changes inside this directory.
- language: python
- framework: fastapi

## Commands

This project uses `uv` for dependency management and task execution.

```bash
# Install / sync dependencies (also creates .venv)
uv sync

# Run the app (auto-reload, binds 0.0.0.0:8000). ./run.sh does both.
uv run uvicorn app.main:app --reload
./run.sh

# Tests
uv run pytest                        # full suite
uv run pytest tests/test_todos.py    # one file
uv run pytest tests/test_todos.py::test_create_todo   # one test
uv run pytest -k "reorder"           # by keyword
uv run pytest -x -vv                 # stop on first failure, verbose
```

`pyproject.toml` sets `pythonpath = ["src"]`, so tests import as `from app.<…>` without needing an editable install. Note: `pytest`/`httpx` are listed as main dependencies (not dev) — this is intentional for workshop simplicity (see comment in `pyproject.toml`).

Demo credentials seeded at startup: `demo@example.com` / `demo123`. The SQLite file `todo.db` is created next to the working directory on first run; delete it to reset state.

## Architecture

### The stack — and why it matters for edits

**HTMX + FastAPI + Jinja2 + Shoelace.** Routes return **HTML fragments**, not JSON. The server is the source of truth for UI state; the browser swaps server-rendered partials into the DOM. This shapes almost every decision:

- Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
- Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context. There is no JSON error envelope.
- Redirects for HTMX requests use the `HX-Redirect` response header (not a 302), because HTMX swaps fragments — a normal redirect would replace the fragment, not the page. See the 401 handler in `src/app/main.py` and the post-login flow in `src/app/routes/auth.py` for the pattern.
- **Out-of-Band (OOB) swaps** are a core idiom. When one action needs to update multiple regions, the route returns a composite partial like `partials/todo_item_with_oob.html` that embeds `hx-swap-oob` markers. Example: toggling a todo updates both the todo row and the sidebar's incomplete-count badge in a single response. Before adding a new interaction, check whether it needs an OOB swap.

### Module layout

```
src/app/
├── main.py           # FastAPI app, lifespan (init_db + seed_demo_data), 401/SQLAlchemy handlers
├── database.py       # SQLAlchemy models (User, TodoList, Todo), engine, get_db dependency
├── utils.py          # Template-exposed helpers: is_overdue, is_due_today, format_date[_input]
├── core/deps.py      # In-memory session store + auth dependencies + HTMX helpers
├── models/           # Pydantic request validation (not ORM)
├── routes/
│   ├── pages.py      # HTML page routes ("/", "/login", "/app", "/app/lists/{id}")
│   ├── auth.py       # /auth/login, /auth/register, /auth/logout
│   ├── todo_lists.py # /api/lists CRUD + /api/lists/reorder
│   └── todos.py      # /api/todos CRUD + /api/todos/search + /api/todos/{id}/toggle|reorder
├── templates/        # Jinja2 (base.html, app.html, login.html, register.html + partials/)
└── static/           # styles.css, app.js, images
```

### SQLAlchemy models (`src/app/database.py`)

Three tables, UUID string PKs, cascade deletes:

- `User` → `TodoList` (`cascade="all, delete-orphan"`)
- `TodoList` → `Todo` (`cascade="all, delete-orphan"`)

Ordering is managed explicitly via an integer `position` column on both `TodoList` and `Todo`, with composite indexes `(user_id, position)` / `(list_id, position)`. **When inserting**, compute `position` as `(MAX(position) + 1)`; see the pattern at `src/app/routes/todos.py:107-113` and `src/app/routes/todo_lists.py:71-77`. **When reordering**, shift the affected range — see `reorder_todo` in `src/app/routes/todos.py:309-356` (single-item move with conditional shift) and `reorder_lists` in `src/app/routes/todo_lists.py:218-258` (bulk reassignment from form-posted ID list).

The engine uses `NullPool` and `check_same_thread=False` because SQLite + FastAPI's threadpool don't mix with default pooling.

### Authentication (intentionally simple)

`src/app/core/deps.py` holds sessions in a **module-level dict** (`sessions: dict[str, dict]`) — they vanish on restart. Passwords are stored **plain text**. This is a deliberate educational simplification documented in the README; do not "fix" it without direction. Use it as the reference pattern:

- `get_current_user_id` — hard dependency, raises 401 on missing/expired session.
- `get_optional_user_id` — soft dependency, returns `None` for anonymous.
- `get_session` — expiring-aware lookup that self-cleans expired entries.
- The global 401 handler in `main.py` converts `HTTPException(status_code=401)` into the right redirect for both HTMX and full-page requests.

### Templates — shared globals

Each router that renders templates re-creates a `Jinja2Templates(directory="src/app/templates")` and attaches `is_overdue`, `is_due_today`, `format_date`, `format_date_input` as **template globals**. If you add a new helper used by templates, register it in every router that renders (currently `pages.py`, `todo_lists.py`, `todos.py`). There is no single shared template instance.

### Tests

`tests/conftest.py` builds an **in-memory SQLite** with `StaticPool` per test, overrides `get_db`, and clears the in-memory `sessions` dict in the `client` fixture. Fixtures compose: `db_session` → `client` → `authenticated_client` (with `test_user`, `test_list`, `test_todo`). Use `authenticated_client` whenever the route requires auth — it sets the `session_id` cookie for you.

## Cross-cutting conventions

- **Ownership check first** in every `/api/lists/{id}` and `/api/todos/{id}` route: see `_verify_list_access` in `src/app/routes/todos.py:26-30`. Todos inherit ownership through their list. A 403/404 HTML error partial is returned on failure.
- **Validation** happens ad-hoc in route handlers (title non-empty, length ≤ 200, priority in `{low, medium, high}`) and returns `partials/error.html`. Pydantic models exist under `src/app/models/` but are not wired into route handlers — do not assume they run.
- **Datetime handling is inconsistent by design** between `utils.is_overdue` (naive `datetime.now()`) and session expiry / `completed_at` (`datetime.now(timezone.utc)`). `Todo.due_date` is stored naive. If touching time logic, read the surrounding code — don't assume UTC.
- **Educational project, not production.** The `todo.db` SQLite file is checked in as sample data.


---


## Current State

See `docs/STATE.md` for current phase, active stories, blockers, and session continuity notes.


---


## Project Document Index

<!-- These paths tell AndThen workflow commands (clarify, spec, plan, trade-off, etc.)
     where this project keeps its documents. Paths are relative to repository root. -->

| Document Type        | Location                            | Notes                                   |
|----------------------|-------------------------------------|-----------------------------------------|
| Product Backlog      | `docs/PRODUCT-BACKLOG.md`           | Feature REQ-IDs and known-defect BUG-IDs; reference both by ID in stories and PRs |
| Roadmap              | `docs/ROADMAP.md`                   | Phase structure with success criteria   |
| Specs & Plans        | `docs/specs/<version-or-feature>/`  | PRDs, implementation plans, FIS, story breakdowns &dagger; |
| ADRs                 | `docs/adrs/`                        | Architecture Decision Records (create on first ADR) |
| Research             | `docs/research/`                    | Trade-off analysis output (create on first entry) |
| Architecture         | This `CLAUDE.md` (`## Architecture`) | Inline — no separate `ARCHITECTURE.md` |
| Stack                | `docs/STACK.md`                     | Technology stack documentation          |
| Ubiquitous Language  | `docs/UBIQUITOUS_LANGUAGE.md`       | Domain glossary — canonical terms, synonyms to avoid |
| Guidelines           | `docs/guidelines/`                  | Development guidelines                  |
| State                | `docs/STATE.md`                     | Cross-session state tracking (current phase, progress, blockers) |
| Learnings            | `docs/LEARNINGS.md`                 | Accumulated project knowledge and error patterns |
| Key Dev Commands     | `docs/KEY_DEVELOPMENT_COMMANDS.md`  | Dev, test, build, deploy commands       |
| Agent Temp           | `.agent_temp/`                      | Temporary agent workspace (reviews, research, QA) |

&dagger; Organized by version or feature name: `docs/specs/{version-or-feature}/prd.md`, `plan.md`, `.technical-research.md`, and per-story FIS files (`s01-*.md`, `s02-*.md`, …) co-located in the same directory — one FIS per story. Standalone specs go directly in `docs/specs/`.


---


## Workflow Rules, Guardrails and Guidelines

### Foundational Rules and Guardrails

_Always fully read and understand this file before doing any work:_ @docs/guidelines/CRITICAL-RULES-AND-GUARDRAILS.md

### Foundational Development Guidelines and Standards

**Always read** relevant guidelines below as _needed_, based on the type of work being done. Review what guidelines are relevant to the task at hand before starting any work that involves coding, code exploration, architecture and solution design, UX/UI, code review, etc.

- _`docs/guidelines/DEVELOPMENT-ARCHITECTURE-GUIDELINES.md`_ when doing development work (coding, architecture, etc.)
- _`docs/guidelines/WEB-DEV-GUIDELINES.md`_ when doing web development work (HTMX partials, route handlers, templates)
- _`docs/guidelines/UX-UI-GUIDELINES.md`_ when doing UX/UI related work (Shoelace components, styles, accessibility)


---


## Project-Specific Guidelines

- **HTMX-first.** Every route that renders should return an HTML partial — see `## Architecture → The stack` above. Do not introduce JSON endpoints unless explicitly asked.
- **Do not "fix" the intentionally simple auth.** Plain-text passwords and in-memory `sessions` dict are deliberate educational choices. See `src/app/core/deps.py` and the README.
- **Pydantic models in `src/app/models/` are _not_ wired into routes.** Validation is ad-hoc in the handlers — do not assume models run.
- **Defects are tracked in `docs/PRODUCT-BACKLOG.md` → Known Defects.** When asked to fix a `BUG-*` ID, read the backlog entry for scope and severity before writing a spec — do not infer a defect's scope from the prompt alone. Reference the `BUG-*` ID in the branch, commit, and PR.


## Visual Validation Workflow

1. Run `./run.sh` (or `uv run uvicorn app.main:app --reload`) and open <http://localhost:8000>.
2. Log in with `demo@example.com` / `demo123` to exercise authenticated routes.
3. For automated checks, prefer `chrome-devtools` MCP or the `agent-browser` CLI (see **Useful Tools** below).
4. When altering interactions that update multiple DOM regions (counts, sidebar, row), verify the OOB swap still fires — check both the primary target and any region marked with `hx-swap-oob`.


---


## Vital Documentation Resources

- `README.md` — quick start, feature list, educational notice
- `docs/STACK.md` — technology stack with versions
- `docs/KEY_DEVELOPMENT_COMMANDS.md` — canonical commands reference
- `docs/UBIQUITOUS_LANGUAGE.md` — domain glossary (Todo, TodoList, OOB Swap, …)
- `docs/LEARNINGS.md` — accumulated gotchas and patterns

**IMPORTANT**: When lookup of external documentation (framework/API references, user guides, etc.) is needed, _always_ execute the documentation lookup in a separate background sub task (use the `andthen:documentation-lookup` agent). This reduces load on the main context window.


---


## Useful Tools and MCP Servers

### Command-line search and exploration
- **ripgrep (rg)**: Fast recursive search — use instead of grep.
- **ast-grep**: Search by AST node types.
- **tree**: Directory structure visualization (`tree -L 2 src/app/`).

### Context7 MCP — library and framework documentation
Up-to-date docs from source. **Only** use via the `andthen:documentation-lookup` agent.

### Fetch MCP — web content retrieval
Retrieves pages as markdown. **Only** use via the `andthen:documentation-lookup` agent.

### Code analysis
- Run `mcp__ide_getDiagnostics` on any file you create or modify. Fix analysis/type errors before calling the task complete.

### Visual validation / browser automation
- **Agent Browser** (`agent-browser` CLI) — quick navigate → snapshot → click/fill loop. See the `agent-browser` skill.
- **Chrome DevTools MCP** — deeper inspection, JS execution, network. See the `chrome-devtools` skill.


---


## Key Development Commands

See `docs/KEY_DEVELOPMENT_COMMANDS.md` for the canonical reference (dev server, tests, visual validation). The `## Commands` section at the top of this file contains the same commands inline for agents reading steering context.
