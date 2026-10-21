---
id: FLAGLITE-REVIEW-001
type: review-record
title: <review scope> review
status: draft
version: 0.1
created: 2026-10-21
updated: 2026-10-21
related-artifacts: FLAGLITE-SPEC-001, FLAGLITE-DESIGN-001
---

# FLAGLITE-REVIEW-001 — <review scope> review

## Review request and frozen scope

Record the gate/transition, exact target artifact IDs/versions or code revision, in/out scope, evidence cutoff, governing criteria, and approval authority.

## Review method and independence

Name critic, reviser, verifier, reviewer mode (`independent`, `partially independent`, `self-review`), source/evidence inspected, and limits. A self-review cannot pass a gate requiring independence.

## Finding register

For each finding, use a stable review-scoped ID and record target location, severity, direct evidence, inference, user/system impact, recommendation/options, owner decision flag, and initial disposition.

## Dispositions and revision

Every finding is `resolved`, `rejected`, `deferred`, `owner-decision-required`, or `accepted-risk`, with evidence, authority, resulting artifact/revision, and revisit condition where applicable. `accepted-risk` is owner-only.

## Rerun and result

Rerun the original scope after accepted changes and record each prior finding as verified resolved, not resolved, accepted risk, or not applicable with reason. Choose `PASS`, `FAIL`, `INCONCLUSIVE`, or `NOT A GATE` per the linked workflow. Record approval and the next action/owner.

## References

Link the reviewed artifacts, governing gate, decisions, resulting revisions, verification evidence, and framework review procedure version.
