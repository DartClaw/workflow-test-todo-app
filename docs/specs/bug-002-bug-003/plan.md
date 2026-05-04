# Implementation Plan: Todo App – BUG-002 and BUG-003

> **PRD**: [`prd.md`](./prd.md)
> **Backlog**: [`../../PRODUCT-BACKLOG.md`](../../PRODUCT-BACKLOG.md)
> **Roadmap**: [`../../ROADMAP.md`](../../ROADMAP.md)
> **State**: [`../../STATE.md`](../../STATE.md)
> **Technical Research**: [`.technical-research.md`](./.technical-research.md)


## Overview
- **Total stories**: 2
- **Phases**: 1
- **Approach**: Ship two thin vertical defect slices that stay independent in user-facing scope while preserving the shared todo row and edit-dialog contract. Execute them serially because both stories touch `src/app/routes/todos.py`, `tests/test_todos.py`, and the same row/dialog hydration seam, even though they do not depend on each other for product behavior.


## Story Catalog

| ID | Name | Phase | Wave | Dependencies | Parallel | Risk | Status | FIS |
|----|------|-------|------|--------------|----------|------|--------|-----|
| S01 | Persist edited due dates in the Todo edit dialog | Defect slices | W1 | - | No | Medium | Spec Ready | `docs/specs/bug-002-bug-003/s01-persist-edited-due-dates.md` |
| S02 | Apply default quick-add Priority at create time | Defect slices | W2 | S01 | No | Low | Spec Ready | `docs/specs/bug-002-bug-003/s02-apply-default-quick-add-priority.md` |

> **Invariant**: each row's `FIS` path is unique – one story maps to exactly one FIS. Stories that would share a spec should have been merged in Step 3's Consolidation Pass.


## Phase Breakdown

### Phase 1: Defect slices
_Both stories are thin and independently demoable, but execution is intentionally serialized because they share the same route module, regression file, and row/dialog hydration seam. `S02` follows `S01` for shared-file safety, not because of a product dependency._

#### S01: Persist edited due dates in the Todo edit dialog
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003/s01-persist-edited-due-dates.md`
**Phase**: Phase 1: Defect slices
**Wave**: W1
**Dependencies**: -
**Parallel**: No
**Risk**: Medium – due-date parsing, visible error handling inside the dialog-target swap, and reopen-state rendering must stay aligned with the existing HTMX partial flow.
**Scope**: Fix the todo update flow so the edit dialog's date input round-trips correctly through save and reopen. Invalid due-date submissions must return the existing `partials/error.html` alert into the form's `hx-target="this"` swap area, leave the dialog open, leave the underlying todo row unchanged, and rely on the unchanged row as the recovery path after the user dismisses the alert and reopens the dialog. This story does not redesign the dialog, change time-zone semantics, or alter unrelated Todo metadata behavior.
**Acceptance Criteria**:
- [ ] Saving a valid due date from the Todo edit dialog persists that date on the Todo record.
- [ ] Reopening the same Todo after save repopulates the edit dialog with the saved due date in the existing `YYYY-MM-DD` date-input format.
- [ ] Clearing the due date and saving leaves the Todo without a due date, and reopening shows an empty due-date field.
- [ ] Submitting an invalid or unsupported due-date value replaces the edit-form swap target with `partials/error.html` using the message `Due date must use YYYY-MM-DD format`, while the dialog stays open and the underlying todo row remains unchanged.
- [ ] An invalid due-date submission leaves any previously saved valid due date unchanged.
- [ ] Automated tests cover the valid save, clear, reopen-state, and invalid-input paths without regressing existing todo update behavior.
**Key Scenarios**:
- Happy: User saves `2025-12-31` from the edit dialog and later reopens the same Todo to see `2025-12-31` prefilled.
- Edge: User clears an existing due date and later reopens the Todo to confirm the field is empty.
- Error: User submits a malformed due date, sees an error partial, and the previously saved date is still present when the Todo is refreshed or reopened.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-dates`, `src/app/templates/app.html`, `src/app/templates/partials/todo_item.html`, `src/app/templates/partials/error.html`

#### S02: Apply default quick-add Priority at create time
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003/s02-apply-default-quick-add-priority.md`
**Phase**: Phase 1: Defect slices
**Wave**: W2
**Dependencies**: S01 (shared-file sequencing only)
**Parallel**: No
**Risk**: Low
**Scope**: Fix the quick-add create flow so todos created with only a title begin with the documented default Priority of `low`. This story focuses on immediate row rendering consistency, edit-dialog reopen consistency, and regression coverage for the create path, building on the shared row/dialog contract already exercised by S01. It does not change Priority options, make the default configurable, or expand quick add beyond its current title-only contract.
**Acceptance Criteria**:
- [ ] Creating a Todo through quick add with only a title stores the Todo with Priority `low`.
- [ ] The created Todo row renders the default Priority state immediately in the returned HTML partial.
- [ ] Opening that quick-added Todo in the edit dialog shows the Priority selector prefilled with `low`.
- [ ] Later edits can still change Priority away from `low` through the existing update flow.
- [ ] Any failure to assign a valid default Priority returns a visible HTML error response consistent with current app patterns rather than creating a partially initialized Todo.
- [ ] Automated tests cover default assignment and reopen-state consistency without regressing existing todo create behavior.
**Key Scenarios**:
- Happy: User quick-adds a title-only Todo and the rendered row immediately shows `Low`.
- Edge: User opens that new Todo in the edit dialog and sees `low` selected before making any changes.
- Follow-up: User later changes Priority to `high` and the normal update flow still works.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr2-apply-default-priority-on-quick-add`, `src/app/templates/partials/todo_list_content.html`, `src/app/templates/partials/todo_item.html`


## Dependency Graph

```text
Dependency arrows:
S01 ──→ S02  (shared-file sequencing only)

Wave assignments:
W1: S01
W2: S02
```


## Risk Summary

| Story | Risk | Concern | Mitigation |
|-------|------|---------|------------|
| S01 | Medium | The UI submits date-only values while the handler currently parses a datetime-local format and hides failures. | Keep the existing HTML-partial contract, parse only the dialog's accepted format, and add regression tests for valid, clear, and invalid inputs. |
| S02 | Low | Quick add and edit-dialog rendering can drift if the default is set only in one layer. | Make create-time defaulting authoritative and verify both the DB value and rendered row/dialog state in tests. |


## Execution Guide

This plan ships fully specced – every story already has a FIS (see the `FIS` column).

1. **Execute the whole bundle**: invoke the `dartclaw-exec-plan` skill on this directory. It runs the per-story `exec-spec → quick-review` pipeline by phase and wave, then a final gap review.
2. **Or execute one story at a time**: invoke the `dartclaw-exec-spec` skill on a single story's FIS for finer control.
3. Phase ordering and `[P]` parallel markers are honored by `exec-plan`; dependencies block waves automatically.
4. After execution, the `dartclaw-exec-plan` skill runs `dartclaw-review --mode gap` on `plan.md` for cross-story coverage validation.

> **Status tracking**: Keep the Story Catalog table and the Phase Breakdown story sections in sync. The `dartclaw-exec-plan` and `dartclaw-exec-spec` skills (via `dartclaw-ops`) write authoritative status into these fields during execution.
