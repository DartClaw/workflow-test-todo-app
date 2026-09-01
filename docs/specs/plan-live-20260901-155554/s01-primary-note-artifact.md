# Primary Note Artifact

**Plan**: docs/specs/plan-live-20260901-155554/plan.json
**Story-ID**: S01

## Feature Overview and Goal

**Intent**: Provide the first required note as an independently verifiable, minimal documentation artifact.

**Expected Outcomes**:

- [OC01] The primary note artifact exists with exactly one non-empty Markdown heading and one non-empty Markdown bullet.
- [OC02] Completing this story leaves the secondary note artifact and every other file unchanged.

## Required Context

- `docs/specs/plan-live-20260901-155554/prd.md#workflow-live-ui-scenario-20260901-155554` – Defines the primary artifact identity, exact two-element content shape, and strict change boundary without permitting implementation paths to be repeated in planning or specification artifacts.

## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01] Primary note has the complete required shape**
  - **Given** the PRD anchor identifies the primary note artifact
  - **When** the story is implemented
  - **Then** that artifact contains exactly one non-empty Markdown heading followed immediately by exactly one non-empty Markdown bullet, with no other content

- [ ] **S02 [OC01] [TI01] Extra or malformed content is rejected**
  - **Given** the primary note artifact is missing either required element, includes an empty element, or contains any additional line
  - **When** its content is validated
  - **Then** validation fails

- [ ] **S03 [OC02] [TI02] Story completion is isolated to the primary note**
  - **Given** the repository state before S01 implementation
  - **When** the story is complete
  - **Then** the primary note artifact is the only changed or newly created file

## Structural Criteria

- [ ] **SC01** The implementation artifact identity remains sourced only from the PRD anchor and is not restated in this specification.

## Scope & Boundaries

### Work Areas

- Primary note artifact delivery surface
- Exact Markdown heading-and-bullet content shape
- Repository change boundary for S01

### What We're NOT Doing

- The secondary note artifact – it belongs exclusively to S02.
- Any additional note content – the PRD requires exactly one heading and one bullet.
- Changes to planning or specification artifacts as delivered implementation – they do not count as the required note.
- Changes to any other project file – the PRD limits this slice to its single artifact.

## Architecture Decision

**Approach**: Treat the PRD anchor as the sole source for the primary artifact identity and keep the delivered document to the required two-line Markdown shape.

## Constraints & Gotchas

- **Critical**: Implementation path names must not appear in planning or specification artifacts. Resolve the primary artifact identity from the Required Context anchor during execution.
- **Constraint**: “One heading and one bullet only” permits no blank line, metadata, explanation, or trailing content in the delivered artifact.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** The primary note artifact has exactly the required two-element Markdown content
  - Resolve the artifact identity from the Required Context anchor; its content must be one non-empty heading immediately followed by one non-empty bullet.
  - **Verify**: `cmd: uv run python -c "from pathlib import Path; import re; source=Path('docs/specs/plan-live-20260901-155554/prd.md').read_text(); target=Path(re.findall(r'notes/[A-Za-z0-9._-]+\.md', source)[0]); lines=target.read_text().splitlines(); assert len(lines) == 2 and re.fullmatch(r'#{1,6} \S.*', lines[0]) and re.fullmatch(r'- \S.*', lines[1])"` – the primary artifact exists and contains only one non-empty heading followed by one non-empty bullet
  - **SATISFIES**: S01, S02, SC01

- [ ] **TI02** S01 changes only its primary note artifact
  - Use the primary artifact identity resolved by TI01; the secondary artifact and all other files remain untouched.
  - **Verify**: `cmd: uv run python -c "from pathlib import Path; import re, subprocess; source=Path('docs/specs/plan-live-20260901-155554/prd.md').read_text(); expected=re.findall(r'notes/[A-Za-z0-9._-]+\.md', source)[0]; changed=[line[3:] for line in subprocess.check_output(['git', 'status', '--short'], text=True).splitlines()]; assert changed == [expected]"` – the primary note artifact is the complete changed-file set
  - **SATISFIES**: S03

## Implementation Observations

_No observations recorded yet._
