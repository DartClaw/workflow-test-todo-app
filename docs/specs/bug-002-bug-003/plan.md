# Implementation Plan: BUG-002 and BUG-003 Defect Fixes

> **PRD**: [`prd.md`](./prd.md)
> **Technical Research**: [`.technical-research.md`](./.technical-research.md)


## Overview
- **Total stories**: 2
- **Phases**: 1
- **Approach**: Keep the two backlog defects as thin vertical slices in the same phase. They are product-independent and can execute in parallel, but the specs call out shared file hotspots so implementers can coordinate around `src/app/routes/todos.py` and `tests/test_todos.py`.


## Story Catalog

| ID | Name | Phase | Wave | Dependencies | Parallel | Risk | Status | FIS |
|----|------|-------|------|--------------|----------|------|--------|-----|
| S01 | Persist edited due dates | Defect restoration | W1 | - | [P] | Medium | Spec Ready | `docs/specs/bug-002-bug-003/s01-persist-edited-due-dates.md` |
| S02 | Apply quick-add default priority | Defect restoration | W1 | - | [P] | Low | Spec Ready | `docs/specs/bug-002-bug-003/s02-apply-quick-add-default-priority.md` |

> **Invariant**: each row's `FIS` path is unique - one story maps to exactly one FIS. Stories that would share a spec should have been merged in Step 3's Consolidation Pass.


## Phase Breakdown

### Phase 1: Defect restoration
_Both stories restore broken authenticated todo metadata flows without redesigning the HTMX-first UI. They can execute in parallel because the product behaviors are independent, but both specs call out the shared route and test hotspots for merge-safe coordination._

#### [P] S01: Persist edited due dates
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003/s01-persist-edited-due-dates.md`
**Phase**: Phase 1: Defect restoration
**Wave**: W1
**Dependencies**: -
**Parallel**: [P]
**Risk**: Medium - the current edit flow spans route parsing, dialog hydration, and rendered row metadata, and the existing failure mode silently swallows invalid date input.
**Scope**: Restore date round-tripping for the existing edit dialog only. Cover save, render, reopen, and intentional clear behavior while preserving the current HTML-partial response pattern and existing auth and ownership checks.
**Acceptance Criteria**:
- [ ] Saving a valid due date from the existing edit dialog re-renders the todo row with the saved date visible.
- [ ] Reopening the same todo after save shows the same due date already populated in the edit dialog, and saving unrelated field changes does not clear it.
- [ ] Saving a blank due date intentionally clears the stored date, and invalid due-date submissions do not return a misleading success response.
**Key Scenarios**:
- Happy: save a due date, then reopen the same todo and see the same value still present.
- Edge: save a due date, edit title or note later without touching the date, and keep the existing date.
- Error: submit an invalid due-date value and keep the previous stored state without a false-success row refresh.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr1-persist-edited-due-dates`, `docs/PRODUCT-BACKLOG.md#known-defects`, `AGENTS.md#the-stack-and-why-it-matters-for-edits`

#### [P] S02: Apply quick-add default priority
**Status**: Spec Ready
**FIS**: `docs/specs/bug-002-bug-003/s02-apply-quick-add-default-priority.md`
**Phase**: Phase 1: Defect restoration
**Wave**: W1
**Dependencies**: -
**Parallel**: [P]
**Risk**: Low
**Scope**: Ensure quick-add creates todos with the documented default priority and prove the stored value flows through both the rendered row and the existing edit dialog. Preserve the current quick-add validation rules, route shape, and edit dialog options.
**Acceptance Criteria**:
- [ ] Quick-add creates a todo with the canonical default priority value already stored.
- [ ] Reopening that todo in the existing edit dialog immediately shows `Low` selected, and the rendered row displays the matching low-priority badge state.
- [ ] Users can still change the priority later through the existing edit dialog without regressing the quick-add default behavior.
**Key Scenarios**:
- Happy: create a todo through quick-add and reopen it to see `Low` already selected.
- Edge: inspect the rendered todo row after quick-add and see the low-priority badge and data attributes already aligned.
- Happy: change that todo to `High` later and persist the explicit user choice normally.
**Asset refs**: `docs/specs/bug-002-bug-003/prd.md#fr2-apply-quick-add-default-priority`, `docs/PRODUCT-BACKLOG.md#known-defects`, `AGENTS.md#project-specific-guidelines`


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
| S01 | Medium | The bug spans persistence, display formatting, and dialog hydration, and the current parse failure is silent. | Spec requires regression coverage for save, reopen, clear, and invalid-input paths, plus explicit alignment with `format_date_input(...)`. |


## Execution Guide

This plan ships fully specced - every story already has a FIS (see the `FIS` column).

1. **Execute the whole bundle**: invoke the `andthen-exec-plan` skill on this directory. It runs the per-story `exec-spec -> quick-review` pipeline by phase and wave, then a final gap review.
2. **Or execute one story at a time**: invoke the `andthen-exec-spec` skill on a single story's FIS for finer control.
3. Phase ordering and `[P]` parallel markers are honored by `exec-plan`; both stories are dependency-free, but the technical research document identifies shared route and test hotspots for coordination.
4. After execution, the `andthen-exec-plan` skill runs `andthen-review --mode gap` on `plan.md` for cross-story coverage validation.

> **Status tracking**: Keep the Story Catalog table and the Phase Breakdown story sections in sync. The `andthen-exec-plan` and `andthen-exec-spec` skills (via `andthen-ops`) write authoritative status into these fields during execution.
