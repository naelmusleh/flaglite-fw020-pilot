# Agent instructions

This is an application repository initialized from Adversarial SDD. Read this file and the canonical `mission.md`, `constitution.md`, `specification.md`, `design.md`, and `backlog.md` before substantive work.

- Keep application code and its product artifacts in this repository. The template source owns reusable procedures, not this application's implementation.
- Treat repository artifacts as the durable source of truth. Maintain stable IDs, versions, links, open-decision records, and gate evidence.
- Do not implement work that is blocked by a failed mandatory gate, unresolved owner decision, missing access, or unmet dependency. State the blocker and the next actionable step.
- AI agents perform authorized documentation and implementation work. The product owner makes material product decisions, accepts residual risk, and authorizes consequential external actions.
- At each coherent, verified task checkpoint, commit only reviewed in-scope files and inspect the staged diff. Push to the authorized feature branch when standing or task-specific push authorization exists; never force-push, bypass branch protection, merge, or deploy under this rule. If checks fail, authorization is absent, or the remote is unavailable, report the exact state and do not claim the change is complete or published.
- Do not claim checks, approvals, deployments, or production readiness without observed evidence.
- Keep `design.md` canonical. Do not run Impeccable `document` at this repository root; use an isolated staging copy and store reviewed generated output in `.impeccable/generated/`.
- Use `python3 scripts/artifacts.py list`, `validate`, and `new` for local artifact management. The helper is a snapshot of the framework tool; structural validation does not prove links, decisions, gate evidence, or app readiness.
- The `.sdd/framework.lock.json` file pins the exact framework commit and digests of the copied validator, handoff checks, gate-run schema, and starter template. Update it only as part of a reviewed framework migration.
- The app-owned `.sdd/required-checks.json` is not framework-locked: maintain its task/acceptance-criterion/platform mapping as product scope changes. The locked schema and `scripts/ci_checks.py` validate and execute required entries. Review command changes as code because pull-request workflows execute them without secrets and with read-only repository permissions.
- Each CI attempt writes a provider/run-attempt/source-SHA/event/ref record and hashed stdout/stderr under an uploaded workflow artifact. Link that exact evidence to the task/gate record; a green status for another SHA, skipped check, local commit, or file-presence claim cannot satisfy G-IMPL/G-RELEASE.
- A passed G-REQ or G-ARCH record requires its corresponding populated manifest under `.sdd/`; the validator checks frozen files and exact digests. A passing validator is not itself a gate pass.
- New version-2 apps store immutable JSON gate-run records under `.sdd/gate-runs/<record_id>.json`. The generated G-INTENT record template starts at `not-ready`; it does not assert a gate result. The validator checks structure and repository-local relationships, not the truth or sufficiency of evidence.
- Add SDD Contract Validation and app-specific required checks to branch protection before claiming they block merges. Do not treat this workflow alone as a release gate.
- Record each change's commit SHA, branch/ref, push outcome, required-check results, and review status in its task milestone.

## Framework procedures

Use the current procedures from the configured Adversarial SDD template source. Record the procedure path/version used in gate and review records.

- Gate catalog: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/docs/framework/GATE-CATALOG-001.md
- Tool and skill catalog: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/docs/framework/TOOL-CATALOG-001.md

- lifecycle: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/lifecycle.md
- discovery: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/product-discovery.md
- adversarial review: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/adversarial-review.md
- CX design: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/cx-design.md
- feasibility and architecture: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/feasibility-architecture.md
- AI engineering execution: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/ai-engineering-execution.md
- implementation quality gates: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/engineering-quality-gates.md
- release and operations: https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/release-operations.md
