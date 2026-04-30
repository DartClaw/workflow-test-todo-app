# Implementation Plan: Todo App Defect Fixes for BUG-002 and BUG-003

> **PRD**: [prd.md](./prd.md)
> **Technical Research**: [.technical-research.md](./.technical-research.md)


## Overview
- **Total stories**: 2
- **Phases**: 1
- **Approach**: Deliver `BUG-002` and `BUG-003` as two thin vertical slices in the same execution wave, with merge-safe ownership separated between the todo update route and the Todo model default plus dedicated regression tests.


## Story Catalog

| ID | Name | Phase | Wave | Dependencies | Parallel | Risk | Status | FIS |
|----|------|-------|------|--------------|----------|------|--------|-----|
| S01 | Persist due-date edits | Defect Repairs | W1 | - | [P] | Medium | Pending | `docs/specs/bug-002-bug-003/s01-persist-due-date-edits.md` |
| S02 | Default quick-add priority | Defect Repairs | W1 | - | [P] | Low | Done | `docs/specs/bug-002-bug-003/s02-default-quick-add-priority.md` |

> **Invariant**: each row's `FIS` path is unique – one story maps to exactly one FIS. Stories that would share a spec should have been merged in Step 3's Consolidation Pass.


## Phase Breakdown

### Phase 1: Defect Repairs
_Both stories are production-facing defect fixes with no functional dependency on each other. They can execute in parallel because the merge-safe plan keeps primary file ownership separate._

#### [P] S01: Persist due-date edits
**Status**: Pending
**FIS**: `docs/specs/bug-002-bug-003/s01-persist-due-date-edits.md`
**Phase**: Phase 1: Defect Repairs
**Wave**: W1
**Dependencies**: -
**Parallel**: [P]
**Risk**: Medium – the current update path silently ignores mismatched input, so the fix must preserve intentional clearing while preventing silent metadata loss.
**Scope**: Correct the todo edit-save-reopen flow so date-only values emitted by the current dialog persist in storage and round-trip back into the dialog. Include regression coverage for valid save, intentional clear, and invalid-input protection. Exclude overdue styling semantics, broader datetime normalization, and any UI redesign.
**Acceptance Criteria**:
- [ ] Saving a todo from the edit dialog with a valid `YYYY-MM-DD` due date persists that value on the Todo record.
- [ ] Reopening the same todo after a successful save shows the saved due date populated in the edit dialog and row metadata.
- [ ] Submitting an intentionally blank due-date value clears an existing due date.
- [ ] Submitting an invalid or unsupported due-date value does not silently overwrite an existing saved due date.
**Key Scenarios**:
- Happy: edit an existing Todo, save `2025-12-31`, reopen it, and see `2025-12-31` still populated.
- Edge: clear a previously saved Due Date and confirm reopen shows the field blank.
- Error: submit an invalid due-date string against a Todo that already has a Due Date and confirm the existing value survives.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md`, `src/app/templates/app.html`, `src/app/templates/partials/todo_item.html`

#### [P] S02: Default quick-add priority
**Status**: Done
**FIS**: `docs/specs/bug-002-bug-003/s02-default-quick-add-priority.md`
**Phase**: Phase 1: Defect Repairs
**Wave**: W1
**Dependencies**: -
**Parallel**: [P]
**Risk**: Low
**Scope**: Ensure quick-add Todo creation produces a stored `low` Priority even when the form submits only `list_id` and `title`, then prove the rendered row and edit dialog reflect that stored default. Include isolated regression coverage for repeated quick-add creation and later manual priority edits. Exclude any change to the available Priority values or to the edit dialog UI structure.
**Acceptance Criteria**:
- [x] Creating a Todo through quick add with title only stores `low` as the effective Priority.
- [x] The newly rendered todo row reflects the same `low` Priority that was stored.
- [x] Opening the edit dialog for a quick-added Todo shows `Low` selected until the user changes it.
- [x] Later edits that change Priority to `medium` or `high` continue to persist normally.
**Key Scenarios**:
- Happy: quick-add a Todo, open edit, and see `Low` selected.
- Edge: quick-add several Todos in succession and confirm every stored Priority is `low`.
- Regression: change a quick-added Todo to `high`, save, reopen, and see `High` selected.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md`, `src/app/templates/app.html`, `src/app/templates/partials/todo_item.html`


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
| S01 | Medium | The current route parses `due_date` with a datetime-local format and swallows `ValueError`, which can fake a successful save while leaving state unchanged. | Keep the fix local to the update path, preserve blank-as-clear behavior explicitly, and add regression coverage for valid, blank, and invalid submissions. |
| S02 | Low | The quick-add flow depends on an implicit priority default that is missing today. | Enforce the default at the Todo model boundary so all creation paths receive a defined baseline without widening the route surface. |


## Execution Guide

This plan ships fully specced – every story already has a FIS (see the `FIS` column).

1. **Execute the whole bundle**: invoke the `andthen-exec-plan` skill on this directory. It runs the per-story `exec-spec → quick-review` pipeline by phase and wave, then a final gap review.
2. **Or execute one story at a time**: invoke the `andthen-exec-spec` skill on a single story's FIS for finer control.
3. Phase ordering and `[P]` parallel markers are honored by `exec-plan`; dependencies block waves automatically.
4. After execution, the `andthen-exec-plan` skill runs `andthen-review --mode gap` on `plan.md` for cross-story coverage validation.

> **Status tracking**: Keep the Story Catalog table and the Phase Breakdown story sections in sync. The `andthen-exec-plan` and `andthen-exec-spec` skills (via `andthen-ops`) write authoritative status into these fields during execution.
