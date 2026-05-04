# Implementation Plan: BUG-002 and BUG-003 Todo Defect Fixes

> **PRD**: [`prd.md`](./prd.md)
> **Backlog**: [`../../PRODUCT-BACKLOG.md`](../../PRODUCT-BACKLOG.md)
> **Roadmap**: [`../../ROADMAP.md`](../../ROADMAP.md)
> **State**: [`../../STATE.md`](../../STATE.md)
> **Technical Research**: [`.technical-research.md`](./.technical-research.md)


## Overview
- **Total stories**: 2
- **Phases**: 1
- **Approach**: Keep the two backlog defects as separate thin vertical slices so each can ship and be reviewed independently, while documenting the shared `todos.py` and `test_todos.py` surfaces that require non-overlapping edits. Both stories are ready to execute in the same wave because they have no functional dependency on each other.


## Story Catalog

| ID | Name | Phase | Wave | Dependencies | Parallel | Risk | Status | FIS |
|----|------|-------|------|--------------|----------|------|--------|-----|
| S01 | Persist Edited Due Dates | Defect Correction | W1 | - | [P] | Medium | Spec Ready | `docs/specs/bug-002-bug-003-todo-edit-and-quick-add/s01-persist-edited-due-dates.md` |
| S02 | Apply Default Priority on Quick Add | Defect Correction | W1 | - | [P] | Medium | Spec Ready | `docs/specs/bug-002-bug-003-todo-edit-and-quick-add/s02-apply-default-priority-on-quick-add.md` |

> **Invariant**: each row's `FIS` path is unique – one story maps to exactly one FIS. Stories that would share a spec should have been merged in Step 3's Consolidation Pass.


## Phase Breakdown

### Phase 1: Defect Correction
_Parallel execution is acceptable because the stories address separate user outcomes and can be kept to non-overlapping hunks even though they share the same route and test modules._

<a id="story-s01"></a>
#### [P] S01: Persist Edited Due Dates
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003-todo-edit-and-quick-add/s01-persist-edited-due-dates.md`
**Phase**: Phase 1: Defect Correction
**Wave**: W1
**Dependencies**: -
**Parallel**: [P]
**Risk**: Medium - touches the existing edit route and must preserve current HTMX fragment behavior while correcting date parsing and reopen state.
**Scope**: Fix the existing todo edit flow so a valid date emitted by the current `type="date"` control persists through save, renders back on the todo row, and is shown again when the user reopens the edit dialog. Include route-level regression coverage for valid-save, clear-date, and malformed-date handling. Exclude quick-add priority behavior, time-of-day support, and edit-dialog redesign.
**Acceptance Criteria**:
- [ ] Saving a valid due date from the edit dialog stores a due date on the Todo record and the updated todo row renders that saved date.
- [ ] Reopening the edit dialog for the same Todo shows the previously saved date in the due-date input.
- [ ] Saving the edit dialog with a blank due-date field clears the stored due date and the todo row no longer renders due-date text.
- [ ] Malformed due-date input does not silently become a different persisted date and does not change unrelated todo fields or authorization behavior.
- [ ] Route-level regression tests cover the supported date-only format and the clear-date path without regressing existing todo update assertions.
**Key Scenarios**:
- Happy: user saves `2025-12-31` in edit and later reopens the same Todo with `2025-12-31` prefilled.
- Edge: user clears an existing due date and the todo row plus reopen flow both show no due date.
- Error: user submits malformed due-date input and receives the standard HTML error handling path without a misleading persisted value.
**Asset refs**: `prd.md#fr1-persist-edited-due-dates`, `src/app/routes/todos.py`, `src/app/templates/app.html`, `src/app/templates/partials/todo_item.html`

<a id="story-s02"></a>
#### [P] S02: Apply Default Priority on Quick Add
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003-todo-edit-and-quick-add/s02-apply-default-priority-on-quick-add.md`
**Phase**: Phase 1: Defect Correction
**Wave**: W1
**Dependencies**: -
**Parallel**: [P]
**Risk**: Medium - touches the quick-add create path in the same route module and must preserve insertion order, validation, and OOB count updates while assigning default priority consistently.
**Scope**: Fix the quick-add todo creation flow so title-only submissions persist `low` as the default Priority immediately and every downstream render path reflects that stored value. Include route-level regression coverage for created records and edit-dialog reopen state. Exclude due-date parsing changes, new quick-add fields, and any change to the priority taxonomy.
**Acceptance Criteria**:
- [ ] Creating a Todo through quick add with only a title stores Priority `low` on the created record.
- [ ] The rendered todo row exposes priority data and visual state consistent with a `low` priority Todo immediately after creation.
- [ ] Reopening a quick-added Todo in the edit dialog shows `low` selected until the user changes it.
- [ ] Existing quick-add validation, Position ordering, ownership checks, and incomplete-count OOB behavior remain unchanged.
- [ ] Route-level regression tests prove the default-priority behavior without depending on S01's due-date fix.
**Key Scenarios**:
- Happy: user quick-adds a title-only Todo and sees `low` reflected on the row and in the edit dialog.
- Edge: multiple quick-add submissions all persist `low` while keeping append order intact.
- Error: empty-title quick add still returns the standard HTML error partial and does not create a Todo.
**Asset refs**: `prd.md#fr2-apply-default-priority-on-quick-add`, `src/app/routes/todos.py`, `src/app/templates/partials/todo_item.html`, `tests/test_todos.py`


## Dependency Graph

```text
Dependency arrows:
S01
S02

Wave assignments:
W1: S01, S02
```


## Risk Summary

| Story | Risk | Concern | Mitigation |
|-------|------|---------|------------|
| S01 | Medium | `update_todo` currently parses a datetime-local value while the edit dialog emits a date-only string, so a targeted fix can easily regress clear-date or reopen behavior | Constrain the work to the existing edit route, dialog field, and row-rendering path; add regression tests for save, clear, and malformed input |
| S02 | Medium | The quick-add path shares `create_todo` and `test_todos.py` with other CRUD coverage, so the default-priority fix must not disturb OOB count updates or ordering | Keep the change inside the quick-add creation defaults and add route-level assertions for created state, rendered row data, and dialog reopen behavior |


## Execution Guide

This plan ships fully specced – every story already has a FIS (see the `FIS` column).

1. **Execute the whole bundle**: invoke the `dartclaw-exec-plan` skill on this directory. It runs the per-story `exec-spec → quick-review` pipeline by phase and wave, then a final gap review.
2. **Or execute one story at a time**: invoke the `dartclaw-exec-spec` skill on a single story's FIS for finer control.
3. Phase ordering and `[P]` parallel markers are honored by `exec-plan`; dependencies block waves automatically.
4. After execution, the `dartclaw-exec-plan` skill runs `dartclaw-review --mode gap` on `plan.md` for cross-story coverage validation.

> **Status tracking**: Keep the Story Catalog table and the Phase Breakdown story sections in sync. The `dartclaw-exec-plan` and `dartclaw-exec-spec` skills (via `dartclaw-ops`) write authoritative status into these fields during execution.
