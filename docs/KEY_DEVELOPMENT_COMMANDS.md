# Key Development Commands

## Running the Application

| Command                                   | Description |
|-------------------------------------------|-------------|
| `./run.sh`                                | Sync deps then start Uvicorn with auto-reload |
| `uv sync`                                 | Install / sync dependencies (creates `.venv`) |
| `uv run uvicorn app.main:app --reload`    | Start dev server with auto-reload (binds `0.0.0.0:8000`) |

Application URL: <http://localhost:8000>

Demo credentials seeded at startup: `demo@example.com` / `demo123`. The SQLite file `todo.db` is created next to the working directory on first run; delete it to reset state.

## Code Quality (Formatting, Linting, Type Checking)

_No formatter/linter is currently wired into the project._ Use the IDE's built-in diagnostics (`mcp__ide_getDiagnostics`) to catch issues on files you create or modify.

## Testing

| Command                                                  | Description |
|----------------------------------------------------------|-------------|
| `uv run pytest`                                          | Run the full suite |
| `uv run pytest tests/test_todos.py`                      | Run one file |
| `uv run pytest tests/test_todos.py::test_create_todo`    | Run one test |
| `uv run pytest -k "reorder"`                             | Filter by keyword |
| `uv run pytest -x -vv`                                   | Stop on first failure, verbose output |

Test config: `pyproject.toml` sets `pythonpath = ["src"]`, so tests import as `from app.<…>` without needing an editable install.

## Build & Deployment

_No deployment target configured._ This is an educational project; `uv run ...` is the canonical run path. A production build would use the hatchling wheel target defined in `pyproject.toml`.

## Visual Validation

| Command / Tool          | Description |
|-------------------------|-------------|
| `./run.sh`              | Launch the app for manual browser testing |
| `chrome-devtools` MCP   | Deeper visual validation, DOM inspection, JS execution |
| `agent-browser` CLI     | Lightweight web automation for snapshot/interact loops |
