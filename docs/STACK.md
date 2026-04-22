# Technology Stack

## Languages

| Language | Version | Notes |
|----------|---------|-------|
| Python   | >=3.11  | Declared in `pyproject.toml` (`requires-python`) |
| HTML     | 5       | Jinja2 templates in `src/app/templates/` |
| CSS      | —       | `src/app/static/styles.css` |
| JavaScript | —     | `src/app/static/app.js` (light, HTMX-driven) |

## Frameworks & Libraries

| Name                       | Version    | Purpose |
|----------------------------|------------|---------|
| FastAPI                    | >=0.115.0  | ASGI web framework — HTML-fragment routes |
| Uvicorn (standard)         | >=0.32.0   | ASGI server (dev + prod) |
| Jinja2                     | >=3.1.0    | Server-rendered HTML templates + partials |
| SQLAlchemy                 | >=2.0.0    | ORM; 3 models (User, TodoList, Todo) with cascade delete + explicit `position` ordering |
| python-multipart           | >=0.0.9    | Form parsing for HTMX POSTs |
| Pydantic (with email extra) | >=2.0.0   | Request-model scaffolding (defined in `src/app/models/`, not currently wired into routes) |
| HTMX                       | —          | Frontend interactivity via HTML attributes; loaded from CDN in `base.html` |
| Shoelace                   | —          | Web components library (loaded from CDN in `base.html`) |

## Infrastructure

| Service | Purpose | Notes |
|---------|---------|-------|
| SQLite  | Single-file relational store | `todo.db` is created at project root; deletable to reset state. Sample DB is checked in |

## External Services

_None._ Self-contained educational project. Frontend CDN for HTMX/Shoelace is the only external dependency at runtime.

## Dev Tools

| Tool       | Purpose                         | Config |
|------------|---------------------------------|--------|
| uv         | Dependency management + task runner | `pyproject.toml`, `uv.lock` |
| hatchling  | Build backend                   | `[build-system]` in `pyproject.toml` |
| pytest     | Test runner                     | `[tool.pytest.ini_options]` in `pyproject.toml`; `pythonpath = ["src"]` |
| httpx      | Test client (async HTTP)        | Used by FastAPI `TestClient` in `tests/conftest.py` |

**Note:** `pytest` and `httpx` are listed as main dependencies (not dev) — intentional for workshop simplicity. See the comment in `pyproject.toml`.
