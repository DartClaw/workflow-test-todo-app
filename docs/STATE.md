# Project State

Last Updated: 2026-08-13

## Current Phase

Phase: AndThen workflow bootstrap
Status: On Track

## Active Stories

| Story | Status | FIS | Notes |
|-------|--------|-----|-------|
| _(none)_ | | | |

## Recently Completed

- **Initial setup** (2026-04-22): AndThen workflow structure initialized (CLAUDE.md sections, docs scaffolding, starter guidelines)
- **S01 BUG-002** (2026-08-13): Edit-dialog due dates now persist and are exposed for prefill on reopen.

## Blockers

_(none)_

## Recent Decisions

- Adopted AndThen workflow (Project Document Index, shared guidelines, specs directory) on top of existing educational FastAPI + HTMX todo app.

## Session Continuity Notes

- Keep the `Commands` and `Architecture` sections of `CLAUDE.md` intact — they serve as the Project Overview for AndThen skills.
- Authentication is **intentionally** simple (plain-text passwords, in-memory sessions). Do not "fix" without explicit direction.
