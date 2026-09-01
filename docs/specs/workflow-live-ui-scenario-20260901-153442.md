# Workflow Live UI Scenario 20260901-153442

## Feature Overview and Goal

**Intent**: Provide the workflow smoke run with a uniquely named, minimal Markdown implementation artifact whose exact shape and change boundary can be published deterministically.

**Expected Outcomes**:

- [OC01] The repository contains `notes/spec-live-20260901-153442.md` with exactly one Markdown heading and one bullet.
- [OC02] The implementation changes no path other than `notes/spec-live-20260901-153442.md`; specification and review artifacts are excluded from this implementation-change boundary.

## Required Context

- `AGENTS.md#smoke-run-boundary` – keep the workflow implementation inside this checkout.
- `docs/guidelines/CRITICAL-RULES-AND-GUARDRAILS.md#core-behavioral-rules` – make the smallest auditable change and verify it before completion.

## Acceptance Scenarios

- [ ] **S01 [OC01] [TI01] Exact two-line Markdown artifact exists at the required path**
  - **Given** the workflow executes this FIS in the fixture repository
  - **When** the implementation is complete
  - **Then** `notes/spec-live-20260901-153442.md` contains exactly two lines: a Markdown heading followed by one Markdown bullet, with no other content

- [ ] **S02 [OC02] [TI01] Implementation change set contains only the required Markdown artifact**
  - **Given** specification and review artifacts are workflow metadata rather than implementation changes
  - **When** the implementation diff is inspected
  - **Then** the only implementation path created or modified is `notes/spec-live-20260901-153442.md`

## Structural Criteria

- [ ] **SC01** The implementation artifact is a regular Markdown file at the exact requested workspace-relative path.

## Scope & Boundaries

### Work Areas

- `notes/` implementation-artifact directory
- `notes/spec-live-20260901-153442.md` file content
- Repository implementation-change boundary, excluding `docs/specs/` and `.agent_temp/reviews/` workflow artifacts

### What We're NOT Doing

- Application code, tests, configuration, and existing documentation are unchanged – the smoke scenario requests only one new note.
- Additional files under `notes/` are excluded – the implementation must create exactly one file.
- Extra headings, bullets, prose, or blank lines are excluded – the requested document shape is exact.

## Architecture Decision

**Approach**: Create one plain Markdown file with two non-empty lines because no application integration or reusable machinery is required.

## Constraints & Gotchas

- **Constraint**: The implementation file must not be used for the FIS or review report – keep workflow artifacts under `docs/specs/` and `.agent_temp/reviews/`.
- **Avoid**: Treating specification or review artifacts as implementation changes – exclude those workflow-only paths when auditing the implementation diff.

## Implementation Plan

### Implementation Tasks

- [ ] **TI01** Required Markdown artifact exists with the exact content shape and isolated implementation change set
  - Create only `notes/spec-live-20260901-153442.md`; choose concise scenario-identifying text for its one heading and one bullet.
  - **Verify**: `cmd: test -f notes/spec-live-20260901-153442.md && test "$(wc -l < notes/spec-live-20260901-153442.md | tr -d ' ')" = 2 && test "$(sed -n '1{/^# [^#].*/p};2{/^- .*/p}' notes/spec-live-20260901-153442.md | wc -l | tr -d ' ')" = 2 && test "$( { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | grep -Ev '^(docs/specs/|\.agent_temp/reviews/)' )" = notes/spec-live-20260901-153442.md` – the exact regular file has one heading line and one bullet line, and no other implementation path differs from HEAD.
  - **SATISFIES**: S01, S02, SC01

## Final Validation Checklist

- [ ] The complete repository status contains no implementation change beyond `notes/spec-live-20260901-153442.md`; the active FIS and its review output are the only permitted workflow artifacts.

## Implementation Observations

_No observations recorded yet._
