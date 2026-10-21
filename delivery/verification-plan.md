---
id: FLAGLITE-VERIFICATION-001
type: verification-plan
title: FlagLite Governance Pilot (Synthetic) verification strategy
status: draft
version: 0.2
created: 2026-10-21
updated: 2026-10-21
related-artifacts: FLAGLITE-SPEC-001, FLAGLITE-DESIGN-001, FLAGLITE-BACKLOG-001, GATE-CATALOG-001, WORKFLOW-QUALITY-001
---

# FLAGLITE-VERIFICATION-001 — FlagLite Governance Pilot (Synthetic) verification strategy

## Scope and quality goals

Identify supported release surfaces, important user outcomes, risk areas, and quality requirements. Do not assume tests or tools apply just because a template mentions them.

## Requirement-to-evidence map

| Requirement/task ID | Risk | Verification level/method | Environment/tool | Evidence location | Owner/frequency | Limits |
| --- | --- | --- | --- | --- | --- | --- |
| <FR/NFR/TASK-ID> | <Impact if wrong> | <Automated/manual/provider/device/security> | <App-specific> | <Path/link> | <Role and cadence> | <What this does not prove> |

## Required-check matrix for implementation tasks

For each implementation task, select the checks required by this application's approved specification, architecture, task acceptance criteria, and quality policy. A template command is not automatically an app requirement. Map each acceptance criterion to its required check(s) or to a manual/operational evidence method. A required check that is not run, is unavailable, fails, or does not cover the recorded revision and scope cannot support a G-IMPL pass. Keep optional checks distinct from required checks.

| Task / criterion ID | Required check ID | Required? | Command or procedure | Tool/runtime version | Revision, paths, and platform scope | Pass condition | Result and evidence link | Limits / reason not applicable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <TASK-ID / criterion> | <CHECK-ID> | <yes/no> | <exact command or repeatable procedure> | <version> | <revision, source paths, platform(s)> | <observable expected result> | <not run/passed/failed + durable evidence path> | <limitation or rationale> |

### Coverage policy, when applicable

Coverage is not presumed mandatory. If this application requires coverage, record the approved rationale and define each item below. Do not claim coverage from a passing test count or infer an application threshold from the template repository.

| Policy field | App-specific value |
| --- | --- |
| Required? and rationale / controlling requirement | <yes/no; requirement or policy ID> |
| Coverage tool/provider and version | <tool/provider and version, or not configured> |
| Included production source paths | <explicit paths/globs> |
| Excluded paths and rationale | <explicit paths/globs and reasons> |
| Measured dimensions | <statements/branches/functions/lines or supported subset> |
| Threshold for each dimension | <explicit percentage or not applicable> |
| Enforcement command and CI job | <exact command/job or not enforced> |
| Evidence location and tested revision | <durable report path and commit/ref> |

If coverage is not configured, record it as `not configured` or `not measured`; do not report 100%, zero, or a pass. If the project adopts the bundled Next.js/Vitest starter, its 100% statements/branches/functions/lines thresholds apply only to the TypeScript/TSX source files included by that repository's Vitest configuration. Python initializer tests in this template run with `unittest` and have no configured coverage threshold. Each initialized app must define its own applicable policy.

## G-IMPL evidence mapping

The task's G-IMPL record must link each acceptance criterion to the required-check matrix row and actual result. Record the source revision, environment, path/platform scope, reviewer, failures or exclusions, and the evidence link. G-IMPL passes only when every criterion has supporting observed evidence and all required checks pass, or when the gate contract permits and the authorized owner explicitly records a scoped residual risk.

## Platform applicability matrix

Mark each platform `in-scope`, `out-of-scope`, or `conditional`. For each in-scope or conditional platform, identify applicable requirement/task IDs, the behavior or feature set, the verification method and environment, and the evidence location. For each out-of-scope platform, record the scope-based reason and whether the exclusion affects feature parity or a release gate. Update this matrix when supported platforms or shared behavior change.

| Platform | Applicability | Requirement/task IDs and behavior | Verification method/environment | Evidence location | Exclusion rationale or condition |
| --- | --- | --- | --- | --- | --- |
| Web | <in-scope/out-of-scope/conditional> | <IDs and behavior> | <browser/build/checks> | <path/link> | <reason/condition> |
| iOS | <in-scope/out-of-scope/conditional> | <IDs and behavior> | <simulator/device/build/checks> | <path/link> | <reason/condition> |
| Android | <in-scope/out-of-scope/conditional> | <IDs and behavior> | <emulator/device/build/checks> | <path/link> | <reason/condition> |

## Applicability

Record whether unit, integration, end-to-end, accessibility, web audit, native audit, security/privacy, performance, resilience, data migration, and operational checks apply. For each omitted class give scope-based rationale and required owner acceptance if the omission affects a release gate.

## Failure and rerun policy

Record how a failed check is triaged, what can be fixed within the task, when a new task/decision is required, and what evidence is needed to rerun the gate.
