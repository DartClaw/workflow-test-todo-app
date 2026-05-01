# Implementation Plan: Todo App – BUG-002 and BUG-003

> **PRD**: [`prd.md`](./prd.md)
> **Backlog**: [`../../PRODUCT-BACKLOG.md`](../../PRODUCT-BACKLOG.md)
> **State**: [`../../STATE.md`](../../STATE.md)
> **Ubiquitous Language**: [`../../UBIQUITOUS_LANGUAGE.md`](../../UBIQUITOUS_LANGUAGE.md)
> **Technical Research**: [`.technical-research.md`](./.technical-research.md)


## Overview
- **Total stories**: 2
- **Phases**: 1
- **Approach**: Restore the two documented Todo metadata defects as thin vertical slices in the existing HTMX flow. Keep stories separate for traceability, but execute them in separate waves because both currently converge on the same route and test modules.


## Story Catalog

| ID | Name | Phase | Wave | Dependencies | Parallel | Risk | Status | FIS |
|----|------|-------|------|--------------|----------|------|--------|-----|
| S01 | Persist edited Due Date | Todo metadata defect fixes | W1 | - | No | Medium | Pending | `docs/specs/bug-002-bug-003/s01-bug-002-persist-due-date.md` |
| S02 | Apply default Priority on quick-add | Todo metadata defect fixes | W2 | - | No | Low | Pending | `docs/specs/bug-002-bug-003/s02-bug-003-default-quick-add-priority.md` |

> **Invariant**: each row's `FIS` path is unique – one story maps to exactly one FIS. Stories that would share a spec should have been merged in Step 3's Consolidation Pass.


## Phase Breakdown

### Phase 1: Todo metadata defect fixes
_Single phase because both fixes are Must/P0 defects in the same authenticated Todo flow. Waves are separated to reduce merge pressure in shared route and test files._

#### S01: Persist edited Due Date
**Status**: Done
**FIS**: `docs/specs/bug-002-bug-003/s01-bug-002-persist-due-date.md`
**Phase**: Phase 1: Todo metadata defect fixes
**Wave**: W1
**Dependencies**: -
**Parallel**: No
**Risk**: Medium - The current server parser expects a different date shape than the edit dialog submits, and invalid values are silently ignored today.
**Scope**: Restore due-date round-trip behavior for the existing edit-todo dialog in the authenticated Todo flow. This story covers persistence, edit-dialog repopulation, and rejection of malformed due-date payloads without introducing new API patterns or changing unrelated due-date styling behavior.
**Acceptance Criteria**:
- [ ] Saving a Todo with a valid date from the existing edit dialog stores the selected calendar date on the Todo record.
- [ ] Reopening the edit dialog for that Todo shows the same stored date in the due-date input.
- [ ] Submitting an empty due-date value continues to clear the stored Due Date.
- [ ] A malformed due-date payload does not return a misleading success state that implies the submitted date persisted.
**Key Scenarios**:
- Happy: Edit an existing Todo, save `2025-12-31`, reopen the dialog, and see `2025-12-31` still loaded.
- Edge: Save the same Todo with the due-date field blank and confirm the reopened dialog has no date selected.
- Error: Submit an unsupported due-date payload and receive the existing HTML error pattern instead of a silent no-op success.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-dates`, `docs/PRODUCT-BACKLOG.md#known-defects`

#### S02: Apply default Priority on quick-add
**Status**: Done
**FIS**: `docs/specs/bug-002-bug-003/s02-bug-003-default-quick-add-priority.md`
**Phase**: Phase 1: Todo metadata defect fixes
**Wave**: W2
**Dependencies**: -
**Parallel**: No
**Risk**: Low - The expected default is already documented and test-covered; the main risk is keeping quick-add minimal while preserving existing HTMX fragment behavior.
**Scope**: Ensure the quick-add creation path assigns the documented default Priority of `low` without adding new inputs to the form. This story covers stored state, rendered output consistency, and edit-dialog prepopulation for Todos created through quick-add.
**Acceptance Criteria**:
- [ ] Creating a Todo through quick-add stores Priority `low` when the user only supplies a title.
- [ ] Opening the edit dialog for that Todo shows `Low` selected in the Priority control.
- [ ] Existing edit flows continue to accept valid `low`, `medium`, and `high` priorities.
- [ ] Quick-add remains a title-only entry path with no new required user input.
**Key Scenarios**:
- Happy: Quick-add a Todo with only a title, then reopen it in the edit dialog and see `Low` selected.
- Edge: Quick-add another Todo in the same list and confirm ordering/OOB behavior still works while the new Todo carries `low`.
- Error: Invalid-title quick-add requests continue to return the existing HTML error partial, not a partially-created Todo.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr2-apply-default-priority-on-quick-add`, `docs/PRODUCT-BACKLOG.md#known-defects`


## Dependency Graph

```text
Dependency arrows:
S01
S02

Wave assignments:
W1: S01
W2: S02
```


## Risk Summary

| Story | Risk | Concern | Mitigation |
|-------|------|---------|------------|
| S01 | Medium | `update_todo` currently parses a datetime-local shape while the dialog submits a date-only value, and the failure path silently preserves stale state. | Require explicit malformed-date handling and add route-level regression tests for save, reopen, clear, and invalid submission paths. |
| S02 | Low | Quick-add uses the same Todo route module as S01, so parallel edits would create churn in shared files. | Keep the story separate but schedule it in W2 after S01; verify both database state and edit-dialog prepopulation. |


## Execution Guide

This plan ships fully specced – every story already has a FIS (see the `FIS` column).

1. **Execute the whole bundle**: invoke the `andthen-exec-plan` skill on this directory. It runs the per-story `exec-spec → quick-review` pipeline by phase and wave, then a final gap review.
2. **Or execute one story at a time**: invoke the `andthen-exec-spec` skill on a single story's FIS for finer control.
3. Phase ordering and `[P]` parallel markers are honored by `exec-plan`; dependencies block waves automatically.
4. After execution, the `andthen-exec-plan` skill runs `andthen-review --mode gap` on `plan.md` for cross-story coverage validation.

> **Status tracking**: Keep the Story Catalog table and the Phase Breakdown story sections in sync. The `andthen-exec-plan` and `andthen-exec-spec` skills (via `andthen-ops`) write authoritative status into these fields during execution.
