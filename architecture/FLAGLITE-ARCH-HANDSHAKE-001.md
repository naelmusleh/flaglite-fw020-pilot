---
id: FLAGLITE-ARCH-HANDSHAKE-001
type: architecture-handshake
title: FlagLite Governance Pilot (Synthetic) Step 2 contract-freezing handshake
status: draft
version: 0.1
created: 2026-10-21
updated: 2026-10-21
related-artifacts: FLAGLITE-SPEC-001, FLAGLITE-BACKLOG-001, GATE-CATALOG-001, CAP-006
---

# Step 2 — Contract Freezing: Architect Handshake

## Gate boundary

This contract governs the Architect's Step 2 contract-freezing phase for the **Bounded Local Functional Alpha** milestone. The Architect MUST work only from approved requirements, recorded decisions, the active architecture scope, and the selected milestone's acceptance criteria. This handshake is not evidence that any gate has passed until its required artifacts and checks are present and reviewed.

## Architect protocol enforcement

- The Architect MUST communicate through repository artifacts only. It MUST NOT emit conversational chatter, preambles, greetings, progress narration, or descriptions of its changes. Its output MUST be raw structural configurations written directly to their required repository paths.
- The Architect MUST NOT expand the approved milestone, invent routes, schemas, dependencies, product behavior, or acceptance criteria. Unresolved decisions and missing evidence remain explicit blockers; they MUST NOT be silently guessed.
- The active alpha MUST remain local and bounded by its approved requirements. No hosted service, cloud account, deployment, production credential, or external integration is implied by this handshake.

## Future hosted schema isolation

Future hosted paradigms, cloud schemas, hosted-provider data models, and associated migration proposals MUST be stored exclusively under `./docs/architecture/future-hosted/`. They MUST NOT be added to, referenced as active requirements from, or otherwise mixed into the active codebase backlog (`backlog.md`), active local-alpha schemas, or implementation contracts. A future hosted proposal does not authorize implementation; it requires a separately approved scope and gate decision before it can affect active work.

## Frozen contract handoff assets

To complete the Architect phase loop, write the OpenAPI contract to `./packages/contracts/openapi.json` and populate `./.sdd/G-ARCH-CONTRACT.json` from `./.sdd/G-ARCH-CONTRACT.json.template`. The template is the canonical app-local schema; `python3 scripts/artifacts.py validate` checks its exact fields and contract version. The manifest MUST:

- Identify contract `G-ARCH-CONTRACT-001`, version `1`, source gate `G-ARCH`, the exact pinned `framework_revision` from `./.sdd/framework.lock.json`, and a specific approved scope.
- Freeze `specification.md`, `design.md`, `backlog.md`, and any other in-scope architecture artifacts using their stable IDs, versions, and SHA-256 digests of exact file bytes.
- Name `./packages/contracts/openapi.json` and its exact SHA-256 digest. Recompute the digest whenever the file changes.
- List exact required verification check IDs, commands, and observable assertions tied to approved requirements. Choose commands for this app's actual stack; do not assume pytest, Vitest, or any other test runner unless the app uses it.
- Use `review_inputs` to enumerate any policy index or domain contract needed by a later adversarial reviewer. Each entry is explicitly allowlisted and frozen by path, artifact ID, version, and digest; use an empty array when no such reviewer input is approved yet.
- Identify an independent architecture review by artifact path, ID, version, digest, reviewer mode, and PASS result.

The Architect MUST replace all template markers and populate the manifest only after the named inputs are frozen. The validator confirms identity, structure, safe paths, exact artifact versions/digests, and explicit check descriptions. It does not run those commands or prove that their assertions are complete; observed execution evidence belongs to the G-IMPL record.

## Active backlog structure invariants

The active system backlog at `backlog.md` MUST be written in short, punchy fragments and organized linearly by architectural layer, in this exact order:

1. **Data / Schema** — frozen entities, fields, constraints, and contract ownership.
2. **Processing Logic** — bounded transformations, validation, and local business rules.
3. **API Routing** — only approved routes, methods, request/response contracts, and failure behavior.
4. **Client Component Layouts** — approved screens/components, states, and contract consumers.

Each backlog fragment MUST trace to an approved requirement or decision and state an observable completion condition. The backlog MUST NOT intermingle future hosted work with active alpha work. Hand-waving structures such as `# TODO`, ellipses (`...`), omitted schemas, invented routes, or placeholder acceptance conditions are system errors. Missing detail MUST be recorded as a blocker or owner decision before dependent implementation begins.

## Phase completion criteria

The Architect phase is ready for review only when all of the following are true:

- `./packages/contracts/openapi.json` contains the complete, bounded contract for the approved local alpha scope.
- `./.sdd/G-ARCH-CONTRACT.json` is a populated JSON instance conforming to the versioned app-local template and matching `framework.lock.json`.
- The manifest freezes the OpenAPI and approved architecture artifacts and names stack-appropriate required checks and observable assertions.
- `backlog.md` follows the required layer order and contains no placeholders, ellipses, or future-hosted work.
- Any proposed future-hosted material is isolated under `./docs/architecture/future-hosted/` and does not alter active alpha scope.
- Architecture review evidence records the exact artifact versions/digests, findings, reviewer independence, and G-ARCH outcome. A missing or failed required check keeps the gate failed or blocked.
