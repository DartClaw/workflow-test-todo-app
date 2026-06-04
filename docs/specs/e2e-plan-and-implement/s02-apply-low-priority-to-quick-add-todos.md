# Feature Implementation Specification

**Plan**: `docs/specs/e2e-plan-and-implement/plan.json`
**Story-ID**: `S02`

## Feature Overview and Goal

**Intent**: Ensure quick-add uses the documented default priority at creation time so every newly created Todo immediately and consistently behaves like a low-priority Todo across the rendered row and the edit dialog.

**Expected Outcomes**:

- [OC01] A quick-add submission that omits `priority` stores `low` as the Todo priority and renders the appended row as Low immediately.
- [OC02] Reopening a quick-added Todo in the edit dialog preselects Low from the Todo's stored priority instead of showing an empty selector.
- [OC03] Existing Todos with an explicit non-low priority still reopen with their own stored priority, proving the fix comes from persisted data rather than a client-side mask.


## Required Context

### From `docs/specs/e2e-plan-and-implement/plan.json` – "S02 scope and notes"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#stories.S02 -->
<!-- extracted: 15e2c3125313a10db880bffbbc6a0e257db1aa37 -->
> Ensure quick-add created todos receive the documented default priority so the new row and the edit dialog both show Low immediately after creation. Includes setting the default at the no-priority creation seam and adding regression coverage for quick-add creation. Excludes changing available priority values or broader priority validation rules for edited todos.
>
> Prefer the source-of-truth no-priority creation seam over a JS fallback so this story stays out of due-date persistence handling.

### From `docs/specs/e2e-plan-and-implement/plan.json` – "Shared decision: Story ownership stays merge-safe"
<!-- source: docs/specs/e2e-plan-and-implement/plan.json#sharedDecisions.story-ownership-stays-merge-safe -->
<!-- extracted: 15e2c3125313a10db880bffbbc6a0e257db1aa37 -->
> S01 owns due-date persistence for edited todos; S02 owns the default priority applied when a todo is created without an explicit priority. Treat any overlap beyond those seams as a re-planning signal, not as permission to widen both stories.

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: 15e2c3125313a10db880bffbbc6a0e257db1aa37 -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
> Story 2: BUG-003 - quick-add todos have no default priority.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects / BUG-003"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: 15e2c3125313a10db880bffbbc6a0e257db1aa37 -->
> BUG-003 | Todos created via the quick-add field have no default priority. Opening the edit dialog shows an empty priority selector instead of the documented default. | Medium | — | Open |


## Deeper Context

- `CLAUDE.md#the-stack--and-why-it-matters-for-edits` – HTMX partial and server-rendered response rules for quick-add responses.
- `CLAUDE.md#tests` – Existing fixture stack and route/integration test placement for Todo coverage.
- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical `Todo` and `Priority` terminology for the spec and implementation.


## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI02] Quick-add persists and renders Low when no priority is submitted**
  - **Given** an authenticated user viewing a TodoList through `partials/todo_list_content.html`
  - **When** they submit the quick-add form with only `list_id` and `title`
  - **Then** the created Todo is stored with `priority == "low"` and the appended row renders Low immediately, including the Low badge and low-priority row metadata used by later interactions

- [ ] **S02 [OC02] [TI02,TI03] Reopening a quick-added Todo shows Low in the edit dialog**
  - **Given** a Todo created through the quick-add flow and appended to the list without a full page reload
  - **When** the user opens that Todo in the edit dialog
  - **Then** the dialog priority select is preselected to Low and does not show an empty state

- [ ] **S03 [OC03] [TI03] Stored medium and high priorities remain visible as their own values**
  - **Given** an existing Todo whose stored priority is `medium` or `high`
  - **When** the user opens the same edit dialog after this story lands
  - **Then** the dialog still preselects that Todo's stored priority instead of collapsing all values to Low

- [ ] **S04 [OC01,OC02] [TI01,TI04] Low remains the quick-add default across a database round-trip**
  - **Given** a user quick-adds a Todo, then returns to the list through an integration-style reload path
  - **When** the app renders that Todo again and the user reopens the edit dialog
  - **Then** the Todo still surfaces as Low, proving the fix comes from persisted data rather than a transient client-side fallback


## Structural Criteria

- [ ] The quick-add path remains a no-priority creation seam: the default is applied in the server-owned creation/persistence path, not by a client-only post-render patch.
- [ ] The existing priority vocabulary and edited-Todo validation surface remain `low`, `medium`, and `high`; this story does not widen into broader priority-rule changes.
- [ ] Regression coverage for BUG-003 lives on disjoint S02-owned test surfaces rather than shared route-test files that would increase merge pressure with S01.


## Scope & Boundaries

### Work Areas
- `src/app/database.py#Todo.priority` – the Todo priority persistence contract where the omitted-priority default can be owned without colliding with S01
- `tests/test_quick_add_priority.py` – dedicated S02-owned regression surface for proving quick-add-created Todos persist and re-render as Low across the user journey
- `tests/test_models.py` or `tests/test_quick_add_priority.py` – disjoint persistence-focused regression coverage for the omitted-priority default without touching shared route-test ownership

### What We're NOT Doing
- Due-date parsing, persistence, or edit-dialog date behavior -- reserved to S01 per the plan's merge-safe ownership split
- New quick-add UI for choosing priority at creation time -- the story keeps quick-add title-only so the server remains the source of truth for omitted priority
- Changes to allowed priority values or broader edited-Todo validation rules -- explicitly excluded by the plan story scope
- Priority badge redesign or CSS rework beyond surfacing the stored Low value -- the story fixes behavior, not presentation taxonomy


## Architecture Decision

**Approach**: Own the default at the persisted `Todo.priority` seam and let the existing quick-add route, row rendering, and edit-dialog hydration consume that stored value end to end without S02 taking ownership of those shared files unless a blocker appears.
**Why this over alternatives**: A model-owned default is the smallest source-of-truth fix, keeps S02 out of S01's shared route and dialog surfaces, and avoids a JS-only mask that could hide null data instead of preventing it.


## Technical Overview

> Synthesis: how components, integration seams, data flow, or tier rationale weave together. **Leave empty** when this is self-evident from Architecture Decision + Code Patterns + per-task descriptions; fill only for multi-component features where the picture isn't obvious from those. Cap at ~10 lines when filled.


## Code Patterns & External References

```text
# type | path#anchor                                      | why needed (intent)
file   | src/app/database.py#Todo.priority               | Preferred ownership seam – persist `low` when creation omits priority
file   | tests/test_quick_add_priority.py                | Dedicated S02-owned regression surface for persisted quick-add behavior
file   | tests/test_models.py                            | Optional disjoint persistence-focused regression surface if a narrow model/default test is needed
```


## Constraints & Gotchas

- **Constraint**: The quick-add form intentionally omits `priority` -- Workaround: keep the default in the server-owned creation seam so the same stored value drives rendering and dialog hydration.
- **Avoid**: Taking ownership of shared route, row-rendering, or edit-dialog files for this story -- Instead: treat the existing quick-add submission, rendered Todo row, and dialog reopening behavior as verification context only, and escalate if the persisted-default seam alone cannot satisfy the scenarios.
- **Critical**: S02 must stay merge-safe with S01 -- Must handle by: preferring the narrow persisted-default seam and disjoint tests, while leaving due-date persistence and shared edit-dialog behavior untouched unless unavoidable.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Omitted quick-add priority resolves to persisted `low` at the narrowest owned seam
  - Prefer `src/app/database.py#Todo.priority` as the ownership seam, keeping the existing quick-add flow as verification context rather than a story-owned implementation surface
  - **Verify**: `uv run pytest tests/test_models.py -k "priority and default"` or `uv run pytest tests/test_quick_add_priority.py -k "default"` proves a newly created `Todo` with no explicit priority persists as `priority == "low"`

- [ ] **TI02** Existing quick-add rendering surfaces Low from persisted data without a story-owned UI fallback
  - Use the existing quick-add POST, rendered Todo row, and edit-dialog reopening behavior as verification context only; do not claim shared runtime/client files unless the persisted-default fix alone fails the scenarios
  - **Verify**: `uv run pytest tests/test_quick_add_priority.py -k "render or row"` proves a quick-added Todo surfaces visible `Low` output and row metadata sourced from persisted priority

- [ ] **TI03** Regression coverage proves the edit dialog reopens persisted priorities without collapsing non-low values
  - Prefer a dedicated `tests/test_quick_add_priority.py` module that quick-adds a Todo, reloads the flow, and separately checks an explicit `high`-priority Todo through the existing render/hydration path
  - **Verify**: `uv run pytest tests/test_quick_add_priority.py -k "dialog or priority"` proves a quick-added Todo reopens as `low` while an explicit `high` Todo still reopens as `high`

### Testing Strategy
> Default test approach: per-task Verify lines + scenario tests scaffolded from Acceptance Scenarios. **Leave empty** when this is sufficient; fill only when the test approach is non-obvious – level allocation (unit/integration/e2e), fixture or harness decisions, or mocking philosophy that scenario tags + Verify lines don't already encode. Use `[TI<NN>]` task tags to map test concerns to producing tasks.


### Validation
> Standard validation (build/test checks, code review, visual validation, and 1-pass remediation) is handled by exec-spec. **Leave empty** when this is sufficient; only add feature-specific validation requirements if the standard levels are insufficient.


### Execution Contract
> Generic exec-spec discipline – task ordering, Verify gating, sub-agent usage, project validation gates, checkbox immediacy – is enforced by exec-spec. **Leave empty** when this is sufficient; fill only for feature-specific execution constraints (cross-task dependencies like "TI03 must complete before TI04", parallelism rules, or special invocation commands).


## Final Validation Checklist
> Acceptance Scenarios, Structural Criteria, and task Verify lines are the standard completion gates. **Leave empty** when these are sufficient; fill only for feature-specific final gates not already covered (e.g. "no new writes to `~/.claude/`", "no orphan migration files in `db/migrate/`").


## Implementation Observations

> _Managed by exec-spec post-implementation – append-only. Tag semantics: see [`data-contract.md`](data-contract.md) (FIS Mutability Contract, tag definitions). AUTO_MODE assumption-recording: see [`automation-mode.md`](automation-mode.md). Spec authors: leave this section empty._

Discovered Requirements entries use this shape:

- **Title**: short imperative phrase
- **Description**: 1-2 sentences on the discovered requirement
- **Rationale**: why it was missed in original spec
- **Interpretation** (AUTO_MODE only): the conservative interpretation chosen and why
- **Traced from**: task ID where the discovery occurred
- **Date**: YYYY-MM-DD

_No observations recorded yet._
