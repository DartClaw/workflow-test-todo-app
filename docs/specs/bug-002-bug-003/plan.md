# Implementation Plan: BUG-002 and BUG-003 Todo Metadata Fixes

> **PRD**: [`prd.md`](./prd.md)
> **Backlog**: [`docs/PRODUCT-BACKLOG.md`](../../PRODUCT-BACKLOG.md)
> **Technical Research**: [`.technical-research.md`](./.technical-research.md)
> **State**: [`docs/STATE.md`](../../STATE.md)
> **Ubiquitous Language**: [`docs/UBIQUITOUS_LANGUAGE.md`](../../UBIQUITOUS_LANGUAGE.md)


## Overview
- **Total stories**: 2
- **Phases**: 1
- **Approach**: Keep the two product defects as separate vertical stories, but sequence them through one execution lane because both land in the same todo route and regression-test surface. Story 1 restores due-date correctness in the edit path first; Story 2 then makes quick-add priority defaults explicit without reopening the due-date contract.


## Story Catalog

| ID | Name | Phase | Wave | Dependencies | Parallel | Risk | Status | FIS |
|----|------|-------|------|--------------|----------|------|--------|-----|
| S01 | Persist Edited Due Date | Metadata Corrections | W1 | - | No | Medium | Spec Ready | `docs/specs/bug-002-bug-003/s01-persist-edited-due-date.md` |
| S02 | Apply Quick-Add Default Priority | Metadata Corrections | W2 | S01 | No | Low | Spec Ready | `docs/specs/bug-002-bug-003/s02-apply-quick-add-default-priority.md` |

> **Invariant**: each row's `FIS` path is unique – one story maps to exactly one FIS. Stories that would share a spec should have been merged in Step 3's Consolidation Pass.


## Phase Breakdown

### Phase 1: Metadata Corrections
_One execution lane. The stories are behaviorally distinct, but they share `src/app/routes/todos.py` and the existing todo regression tests, so sequential waves reduce merge churn and keep proof-of-work narrow._

#### S01: Persist Edited Due Date
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003/s01-persist-edited-due-date.md`
**Phase**: Phase 1: Metadata Corrections
**Wave**: W1
**Dependencies**: -
**Parallel**: No
**Risk**: Medium - The current edit dialog posts a date-only value while the route parses a datetime-local format, so the fix must align the contract without regressing clear-date behavior or HTMX fragment updates.
**Scope**: Fix the authenticated todo edit-save path so a due date submitted from the existing edit dialog persists and comes back when the same Todo is rendered or reopened. Include visible rejection for malformed due-date input on this route, and keep the existing HTML partial response model intact. Exclude broader date classification work such as overdue and due-today styling.
**Acceptance Criteria**:
- [ ] Saving a valid due date from the edit dialog stores it on the Todo and reopening the same Todo shows the same date populated.
- [ ] Saving title or note changes alongside a due date preserves all valid edits in one save.
- [ ] Clearing an existing due date removes it and reopening the dialog shows an empty due-date field.
- [ ] Malformed due-date input on the covered save path returns a visible HTML error instead of a false-success save.
**Key Scenarios**:
- Happy: save `2025-12-31` from the edit dialog, then reopen and see `2025-12-31`.
- Edge: clear an existing due date and verify the rendered Todo no longer carries due-date metadata.
- Error: submit a malformed due-date string and receive `partials/error.html` rather than a silently dropped value.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-date`, `docs/PRODUCT-BACKLOG.md#known-defects`

#### S02: Apply Quick-Add Default Priority
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003/s02-apply-quick-add-default-priority.md`
**Phase**: Phase 1: Metadata Corrections
**Wave**: W2
**Dependencies**: S01
**Parallel**: No
**Risk**: Low - The data model and edit dialog already assume `low` as the default, but the quick-add create path currently omits it. The main risk is keeping the change scoped to quick add while preserving OOB count updates and edit-dialog metadata.
**Scope**: Ensure the quick-add todo creation path persists `low` as the default Priority at creation time so the rendered Todo row and edit dialog always start from a valid value. Include regression coverage for create and reopen flows. Exclude any change to explicit priority selection in the edit dialog or new defaulting rules beyond quick add.
**Acceptance Criteria**:
- [ ] A Todo created through quick add persists with `low` priority immediately.
- [ ] Reopening that Todo in the edit dialog shows `low` selected unless the user later saved a different priority.
- [ ] The rendered Todo row continues to display the expected priority badge and metadata after quick add.
- [ ] Existing title validation, ownership checks, and OOB incomplete-count behavior remain unchanged for quick add.
**Key Scenarios**:
- Happy: quick-add a Todo with only a title, then open edit and see `low` selected.
- Edge: quick-add a Todo, later save `high`, then reopen and see the explicit override preserved.
- Regression: quick-add still updates the list count and returns the normal row partial.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr2-apply-quick-add-default-priority`, `docs/PRODUCT-BACKLOG.md#known-defects`


## Dependency Graph

```text
Dependency arrows:
S01 ──→ S02

Wave assignments:
W1: S01
W2: S02
```


## Risk Summary

| Story | Risk | Concern | Mitigation |
|-------|------|---------|------------|
| S01 | Medium | Edit dialog `type="date"` posts `YYYY-MM-DD`, but `update_todo` currently parses `"%Y-%m-%dT%H:%M"` and silently keeps old state on `ValueError`. | Lock the accepted input contract to the existing date control, add explicit invalid-input error handling, and prove clear/save/reopen paths in route tests. |
| S02 | Low | Story touches the same route module and test surface as S01 even though the product behavior is separate. | Sequence after S01 and keep the implementation limited to quick-add defaults plus render/edit regression checks. |


## Execution Guide

This plan ships fully specced – every story already has a FIS (see the `FIS` column).

1. **Execute the whole bundle**: invoke the `andthen-exec-plan` skill on this directory. It runs the per-story `exec-spec → quick-review` pipeline by phase and wave, then a final gap review.
2. **Or execute one story at a time**: invoke the `andthen-exec-spec` skill on a single story's FIS for finer control.
3. Phase ordering and parallel markers are honored by `exec-plan`; this bundle intentionally keeps both stories non-parallel because they share the same route and test module.
4. After execution, the `andthen-exec-plan` skill runs `andthen-review --mode gap` on `plan.md` for cross-story coverage validation.

> **Status tracking**: Keep the Story Catalog table and the Phase Breakdown story sections in sync. The `andthen-exec-plan` and `andthen-exec-spec` skills (via `andthen-ops`) write authoritative status into these fields during execution.
