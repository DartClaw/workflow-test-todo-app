# Implementation Plan: Todo App - BUG-002 and BUG-003 Metadata Fixes

> **PRD**: [`prd.md`](./prd.md)
> **Backlog**: [`docs/PRODUCT-BACKLOG.md`](../../PRODUCT-BACKLOG.md)
> **State**: [`docs/STATE.md`](../../STATE.md)
> **Glossary**: [`docs/UBIQUITOUS_LANGUAGE.md`](../../UBIQUITOUS_LANGUAGE.md)
> **Technical Research**: [`.technical-research.md`](./.technical-research.md)

## Overview
- **Total stories**: 2
- **Phases**: 2
- **Approach**: Keep `BUG-002` and `BUG-003` as separate vertical slices, but sequence them by phase because both concentrate in `src/app/routes/todos.py` and `tests/test_todos.py`. Phase 1 restores trustworthy Due Date persistence in the edit dialog; Phase 2 fixes quick-add Priority defaults without expanding the UI surface.

## Story Catalog

| ID | Name | Phase | Wave | Dependencies | Parallel | Risk | Status | FIS |
|----|------|-------|------|--------------|----------|------|--------|-----|
| S01 | BUG-002 Persist Edit-Dialog Due Date | Phase 1: Metadata Persistence | W1 | - | No | Medium | Spec Ready | `docs/specs/bug-002-bug-003-todo-metadata-fixes/s01-bug-002-persist-edit-dialog-due-date.md` |
| S02 | BUG-003 Apply Quick-Add Default Priority | Phase 2: Metadata Defaults | W1 | - | No | Low | Spec Ready | `docs/specs/bug-002-bug-003-todo-metadata-fixes/s02-bug-003-apply-quick-add-default-priority.md` |

> **Invariant**: each row's `FIS` path is unique - one story maps to exactly one FIS. Stories that would share a spec should have been merged in Step 3's Consolidation Pass.

## Phase Breakdown

### Phase 1: Metadata Persistence
_Execute first because BUG-002 is the higher-severity user-trust defect and carries the only new validation branch in this bundle._

#### S01: BUG-002 Persist Edit-Dialog Due Date
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003-todo-metadata-fixes/s01-bug-002-persist-edit-dialog-due-date.md`
**Phase**: Phase 1: Metadata Persistence
**Wave**: W1
**Dependencies**: -
**Parallel**: No
**Risk**: Medium - the update route currently expects a datetime-local format and silently ignores parse failures, so the fix must preserve stored state while surfacing an HTML error.
**Scope**: Restore the existing edit dialog's Due Date persistence path from form submit through stored `Todo.due_date`, row rerender, and dialog reopen. Include explicit clear behavior and visible invalid-input handling for unparseable date payloads. Exclude UI redesign, datetime support, and unrelated overdue/due-today styling fixes.
**Acceptance Criteria**:
- [ ] Saving an existing Todo with a valid date-only Due Date from the edit dialog persists that date on the record.
- [ ] After a successful save, the returned todo row shows the saved Due Date and reopening the edit dialog prepopulates the same `YYYY-MM-DD` value.
- [ ] Clearing an existing Due Date and saving removes the stored value and reopens the dialog with a blank Due Date field.
- [ ] An unparseable Due Date payload returns the standard HTML error partial and leaves the previously stored Due Date unchanged.
**Key Scenarios**:
- Happy: save a valid edit-dialog Due Date, see the row rerender with the new date, then reopen and confirm the same value is prefilled.
- Edge: clear an existing Due Date, save, and reopen to confirm the field stays blank.
- Error: submit an unsupported Due Date payload and receive visible error feedback without mutating the stored Todo.
**Asset refs**: `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#fr1-persist-due-dates-from-the-edit-dialog`, `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#user-flows`, `docs/PRODUCT-BACKLOG.md#known-defects`

### Phase 2: Metadata Defaults
_Execute second to keep the quick-add default fix independent while avoiding concurrent edits in the shared todo route and regression test file._

#### S02: BUG-003 Apply Quick-Add Default Priority
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003-todo-metadata-fixes/s02-bug-003-apply-quick-add-default-priority.md`
**Phase**: Phase 2: Metadata Defaults
**Wave**: W1
**Dependencies**: -
**Parallel**: No
**Risk**: Low
**Scope**: Ensure the quick-add create path persists `low` Priority when the user submits only a title, and prove that the returned todo row and later edit dialog reopen reflect that stored default. Preserve current title-only quick-add UX and existing explicit `medium`/`high` update behavior. Exclude new quick-add controls, schema changes unrelated to defaulting, and changes to unrelated Todo metadata flows.
**Acceptance Criteria**:
- [ ] Creating a Todo through quick-add with only a title persists `low` Priority on the new record.
- [ ] The returned todo row renders the `low` Priority state consistently, including the row class, badge, and row dataset used for dialog reopen.
- [ ] Opening the edit dialog for a quick-add-created Todo shows `low` as the selected Priority.
- [ ] Existing flows that explicitly set `medium` or `high` Priority continue to preserve the user-selected value.
**Key Scenarios**:
- Happy: quick-add a title-only Todo and confirm the new row renders with `low` Priority.
- Edge: open the edit dialog immediately after quick-add and confirm `low` is preselected.
- Regression: later update the same Todo to `medium` or `high` and confirm the explicit user choice still persists.
**Asset refs**: `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#fr2-apply-default-priority-to-quick-add-todos`, `docs/specs/bug-002-bug-003-todo-metadata-fixes/prd.md#user-flows`, `docs/PRODUCT-BACKLOG.md#known-defects`

## Dependency Graph

The two stories are functionally independent. Phase sequencing is intentional shared-file conflict avoidance, not a product dependency.

```text
Dependency arrows:
S01
S02

Phase / wave assignments:
Phase 1 / W1: S01
Phase 2 / W1: S02
```

## Risk Summary

| Story | Risk | Concern | Mitigation |
|-------|------|---------|------------|
| S01 | Medium | `update_todo()` currently parses the wrong Due Date format and silently preserves stale state on parse errors. | Align parsing with the existing date-only dialog contract, return `partials/error.html` on invalid payloads, and add regression tests for save, clear, and error paths. |
| S02 | Low | Quick-add omits `priority` inside the same route/test module already touched by S01. | Keep the fix scoped to `create_todo()`, prove the rendered row carries `low`, and extend regression tests without widening the UI flow. |

## Execution Guide

This plan ships fully specced - every story already has a FIS (see the `FIS` column).

1. **Execute the whole bundle**: invoke the `andthen-exec-plan` skill on this directory. It runs the per-story `exec-spec -> quick-review` pipeline by phase and wave, then a final gap review.
2. **Or execute one story at a time**: invoke the `andthen-exec-spec` skill on a single story's FIS for finer control.
3. Phase ordering and `[P]` parallel markers are honored by `exec-plan`; dependencies block waves automatically.
4. After execution, the `andthen-exec-plan` skill runs `andthen-review --mode gap` on `plan.md` for cross-story coverage validation.

> **Status tracking**: Keep the Story Catalog table and the Phase Breakdown story sections in sync. The `andthen-exec-plan` and `andthen-exec-spec` skills (via `andthen-ops`) write authoritative status into these fields during execution.
