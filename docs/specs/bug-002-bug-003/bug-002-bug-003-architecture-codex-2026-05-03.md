# Architecture Review: bug-002-bug-003

## Executive Summary
This review covers the S01 implementation artifacts introduced on the current branch against the `docs/specs/bug-002-bug-003` plan scope.
I found 1 finding total, all LOW severity, all in documentation/state synchronization and no blocking architectural violations in the changed route implementation.
The most critical issue is inconsistent story status signals between `plan.md` and `docs/STATE.md` after the S01 work was recorded as complete.
The highest-impact remediation is to keep all story-tracking fields synchronized so `andthen-exec-plan` and future automation reads deterministic inputs.

## How to Read This Report
- **Metrics / dashboard**: `Ca` (incoming deps), `Ce` (outgoing deps), `I` (instability, 0 stable to 1 volatile), `A` (abstractness), `D` (distance from main sequence, 0 best).
- **C4 levels**: Context = system-level, Container = runtime/build unit, Component = module/package, Code = file/function.
- **Principles**: ADP = acyclic dependencies, SDP = dependencies must go from unstable to stable, SAP = stable packages should be abstract.
- **Zones**: Zone of Pain indicates high blast radius for small changes; Zone of Uselessness is over-abstraction in unstable packages.
- **Connascence**: CoN name coupling is the weakest and often acceptable; dynamic connascence (CoE/CoV/CoTm/CoI) carries higher architectural risk.

## Metrics Dashboard
| Package | Ca | Ce | I | A | D | Zone | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| src.app.routes | 2 | 4 | 0.67 | 0.00 | 0.33 | Watch | Route module remains a thin orchestration layer over request/DB/template boundaries. |
| tests | 0 | 2 | 1.00 | 0.00 | 0.95 | Uselessness watch | Test module is an execution consumer and should not influence runtime composition. |

## Findings

### ARCH-001: Workflow status fields for the same story are inconsistent across plan and state docs

**Severity**: LOW
**Dimension**: governance
**C4 Level**: Context
**Category**: Convention

**Evidence**: `docs/specs/bug-002-bug-003/plan.md` marks S01 as `Done` in the catalog line 17, but the same section describes `#### [P] S01` as `Status: Spec Ready` at line 29, while `docs/STATE.md` lists S01 as `Spec Ready` at line 14. This leaves one feature cycle with three competing states for the same story.

**Impact**: The state machine used by the workflow tooling can read different signals depending on source, increasing the chance of skipped tasks and inaccurate gap-check sequencing.

**Recommendation**: Enforce a single canonical status source of truth for each active story, then have one place of truth drive all status updates for `docs/STATE.md` and `docs/specs/**/plan.md` during this implementation step.

**Fitness Function**: Add a lightweight consistency check that fails when a story has more than one status value across `STATE.md` and the target plan’s Story Catalog / phase sections before execution continues.

**Fix Prompt**: Update `docs/STATE.md` and `docs/specs/bug-002-bug-003/plan.md` to the same concrete status for S01, then re-run a pre-commit doc-check that validates one-to-one status parity.

## Dependency Graph

- `src.app.routes` imports `app.core.deps`, `app.database`, `app.utils`, `fastapi`, and `sqlalchemy` (outgoing edges to app internals and stable framework packages).
- `tests` imports `app.database` and `datetime` helpers only.
- No package-level cycles are introduced in this branch.
- Leaves: `tests` (consumer). Foundations: `app.database`, framework libraries.

## Decomposition Recommendations
No merge-safe decomposition changes are required in this bounded diff. Keep the S01 route helper extraction as-is.

## Proposed Fitness Functions
1. **status_parity_check**
   - **Checks**: each active story has one status and that status is identical in `docs/STATE.md` and the target plan story sections.
   - **Threshold**: zero drift entries.
   - **Governance level**: Repo CI or pre-merge workflow.
   - **Addresses**: `ARCH-001`

2. **plan_delta_check**
   - **Checks**: if a changed package is touched (e.g., `src/app/routes/todos.py`), required stories in the plan are marked `In Progress` or `Done` in both status registers at commit time.
   - **Threshold**: no unresolved “Spec Ready” when implementation and tests changed in the same story scope.
   - **Governance level**: Review gate.
