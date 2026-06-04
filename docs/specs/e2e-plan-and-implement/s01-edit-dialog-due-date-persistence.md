# Edit-dialog due date persistence

**Plan**: docs/specs/e2e-plan-and-implement/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Ensure a due date chosen in the edit dialog survives save and round-trips back into the dialog so users can trust date edits on existing todos.

**Expected Outcomes**:

- [OC01] Saving a valid date from the edit dialog persists that date and shows it again in both the todo row and the dialog.
- [OC02] Clearing the date from the edit dialog removes the stored due date cleanly.
- [OC03] The update path no longer silently drops due-date changes because it expects the wrong input format.


## Required Context

### From `docs/specs/e2e-plan-and-implement/prd.md` – "Product Feature Document"
<!-- source: docs/specs/e2e-plan-and-implement/prd.md#product-feature-document -->
<!-- extracted: de827ca -->
> Fix BUG-002 and BUG-003 from docs/PRODUCT-BACKLOG.md (Known Defects section) as two independent, thin stories.
>
> Story 1: BUG-002 - due dates set in the edit dialog do not persist after save.
>
> Keep each story isolated to its own files; they must merge without conflict.

### From `docs/PRODUCT-BACKLOG.md` – "Known Defects"
<!-- source: docs/PRODUCT-BACKLOG.md#known-defects -->
<!-- extracted: de827ca -->
> BUG-002 | Due dates set via the edit dialog do not persist. After saving and reopening the dialog, the date field is empty. The parsing path silently swallows format mismatches. | High | — | Open |

### From `CLAUDE.md` – "The stack — and why it matters for edits"
<!-- source: CLAUDE.md#the-stack--and-why-it-matters-for-edits -->
<!-- extracted: de827ca -->
> Routes return `templates.TemplateResponse(...)` with a partial from `templates/partials/`, not Pydantic models.
>
> Error responses are HTML too: `partials/error.html` rendered with a `{"error": "..."}` context.


## Deeper Context

- `docs/UBIQUITOUS_LANGUAGE.md#todo-domain` – Canonical meaning of Todo, Due Date, and Priority terms used in code and the spec.
- `CLAUDE.md#templates--shared-globals` – Reminder that `format_date_input` is already registered in template globals and is the current round-trip format for date inputs.
- `docs/STACK.md#frameworks-libraries` – FastAPI + Jinja2 + SQLAlchemy baseline for route, template, and ORM behavior.


## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01,TI02] Saved due date round-trips through the edit dialog**
  - **Given** an existing todo without a due date in a list the user owns
  - **When** the user opens the edit dialog, chooses `2025-12-31`, saves, and reopens the dialog
  - **Then** the todo row shows the due date and the dialog input value is `2025-12-31`

- [ ] **S02 [OC02] [TI01,TI02] Clearing the date removes the stored due date**
  - **Given** an existing todo with due date `2025-12-31`
  - **When** the user clears the edit dialog date input and saves
  - **Then** the persisted todo has no due date, the row no longer renders a due-date badge, and reopening the dialog shows an empty date input

- [ ] **S03 [OC03] [TI01] Date-only form submissions are accepted by the update path**
  - **Given** the edit dialog submits an HTML `type="date"` value in `YYYY-MM-DD` format
  - **When** `PUT /api/todos/{id}` handles that request
  - **Then** the server stores the chosen date instead of swallowing the change because it expected a datetime-local string

- [ ] **S04 [OC03] [TI03] Malformed due-date payloads fail visibly instead of silently preserving stale state**
  - **Given** an existing todo with a stored due date
  - **When** a client submits a malformed `due_date` value that does not match the accepted edit-dialog format
  - **Then** the response is the standard HTML error partial and the existing stored due date remains unchanged


## Structural Criteria

- [ ] Existing title, note, and priority updates through `PUT /api/todos/{id}` remain unchanged while due-date handling is corrected.
- [ ] Due-date values continue to round-trip through `format_date_input` as `YYYY-MM-DD` so row data attributes and dialog state stay aligned.
- [ ] Regression coverage for BUG-002 lives in a story-owned test surface and exercises save, clear, and malformed-input behavior against the in-memory SQLite fixtures.


## Scope & Boundaries

### Work Areas
- Edit-path due-date parsing and validation in `src/app/routes/todos.py`
- Todo row and dialog date round-trip surface exposed by `src/app/templates/partials/todo_item.html`
- Story-owned BUG-002 regression coverage under `tests/`

### What We're NOT Doing
- Quick-add priority defaults or create-path behavior -- reserved for BUG-003 / S02.
- Due-today or overdue styling fixes -- tracked separately as BUG-004.
- Converting the edit dialog to datetime-local inputs -- the bug is in the existing date-only contract.
- Broad Pydantic-route migration for todo validation -- the app currently validates ad hoc in route handlers.


## Architecture Decision

**Approach**: Align the todo update handler with the existing date-only edit-dialog contract and use the app’s normal HTML error partial when the date payload is malformed.
**Why this over alternatives**: It fixes the reported regression at the server boundary without widening the UI or dragging unused request models into live route code.


## Technical Overview

The dialog already emits date-only values and the row already serializes stored dates back into date inputs. The failure is localized to the update-path parser expecting the wrong shape, so the fix should stay on that path and prove the round-trip with dedicated regression coverage.


## Code Patterns & External References

```text
# type | path#anchor or url | why needed (intent)
file | src/app/routes/todos.py#update_todo | Existing todo edit flow, validation order, and mutation boundary to preserve
file | src/app/utils.py#format_date_input | Canonical `YYYY-MM-DD` serialization for date inputs and row data attributes
file | src/app/templates/partials/todo_item.html:1-40 | Proof surface for dialog reopen state and row-level due-date rendering
```


## Constraints & Gotchas

- **Constraint**: Todo route handlers return HTML partials, not JSON -- Workaround: preserve the existing `partials/error.html` pattern for malformed edit payloads.
- **Avoid**: Accepting datetime-local input shapes on the update path -- Instead: honor the existing `type="date"` dialog contract and its `YYYY-MM-DD` serialization.
- **Critical**: Ownership and authorization checks must remain ahead of all mutation logic -- Must handle by: keeping the current access-verification flow intact.


## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Edit-path due dates persist from date-only dialog submissions
  - Keep the existing ownership and title-validation flow in `src/app/routes/todos.py#update_todo`; align due-date parsing with the current `type="date"` dialog contract and `src/app/utils.py#format_date_input`.
  - **Verify**: `uv run pytest tests/test_bug_002_due_date_persistence.py -k "save or round_trip"` proves saving "2025-12-31" stores the date and the returned HTML exposes the same date for dialog reopen state.

- [ ] **TI02** Removing a due date clears both storage and rendered row state
  - Reuse the current empty-string clear branch in `src/app/routes/todos.py#update_todo`; the returned partial and reopen data attributes must agree that no due date remains.
  - **Verify**: `uv run pytest tests/test_bug_002_due_date_persistence.py -k "clear"` proves persisted `due_date` becomes `None` and the rendered row no longer includes the due-date surface.

- [ ] **TI03** Malformed due-date payloads are rejected predictably
  - Follow the app-wide HTML error pattern described in `CLAUDE.md#the-stack--and-why-it-matters-for-edits`; keep the todo unchanged when parsing fails rather than silently preserving stale state after a partial mutation.
  - **Verify**: `uv run pytest tests/test_bug_002_due_date_persistence.py -k "invalid"` returns the HTML error partial and leaves the stored due date unchanged.

### Testing Strategy

- [TI01,TI02,TI03] Add BUG-002 regression coverage in a dedicated test file so this story does not consume BUG-003's test ownership or depend on shared edits in `tests/test_todos.py`.

### Validation

- Reopen an edited todo in the browser after saving `2025-12-31`, then after clearing it, and confirm the date input value matches persisted state in both directions.

### Execution Contract

- Keep production-file ownership on the edit/update path. If the fix requires touching quick-add creation or priority-default surfaces, stop and re-scope with S02 instead of widening this story.


## Final Validation Checklist

- [ ] Save, reopen, clear, and malformed-input edit flows all behave correctly without consuming S02's create/default ownership surface.


## Implementation Observations

_No observations recorded yet._
