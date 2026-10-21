# FlagLite Governance Pilot (Synthetic)

**Project status:** Ideation
**Active gate:** None; discovery has not started
**Next action:** Give your AI agent the app idea, intended user, problem evidence, desired outcome, and known constraints. Ask it to draft `mission.md` and lead the [product discovery workflow](https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/product-discovery.md) in this repository.
**Canonical status source:** [`backlog.md`](backlog.md)

This repository is the source of truth for FlagLite Governance Pilot (Synthetic): its product decisions, code, and delivery evidence belong here. It was initialized from the reusable [Adversarial SDD template](https://github.com/naelmusleh/adversarial-sdd-boilerplate/tree/484c4cc3c7d1c0962439d11197fc09473845c163); there is no framework service to install or operate. The exact source revision is recorded in [`.sdd/framework.lock.json`](.sdd/framework.lock.json). No gate has passed and no product decisions are pre-approved by this starter.

## Local artifact commands

This repository includes the dependency-free artifact helper. Run it from this repository to list, validate, or create app artifacts:

```sh
python3 scripts/artifacts.py list
python3 scripts/artifacts.py validate
python3 scripts/artifacts.py new decision FLAGLITE-DECISION-002 "Choose the initial data-retention rule"
```

The helper discovers this repository's canonical SDD files and artifact folders; it does not read or change the separate framework checkout.

## Start here

1. Give the agent the app idea, intended user, problem evidence, desired outcome, and known constraints. The agent drafts [`mission.md`](mission.md) with you and records evidence, assumptions, exclusions, and unresolved decisions.
2. Have the agent follow the [product discovery workflow](https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/product-discovery.md) to draft `constitution.md`, `specification.md`, and `backlog.md`, then return only material decisions and the G-INTENT/G-REQ evidence for your review.
3. Keep `design.md` as the canonical experience contract. Use the [CX design workflow](https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/cx-design.md) and link visual review evidence there.
4. Use [`backlog.md`](backlog.md) for prioritized, approved implementation work and the [lifecycle workflow](https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/workflows/lifecycle.md) for the next stage.

## Gates and tools

Use the framework's [gate catalog](https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/docs/framework/GATE-CATALOG-001.md) for transition criteria and its [tool and skill catalog](https://github.com/naelmusleh/adversarial-sdd-boilerplate/blob/484c4cc3c7d1c0962439d11197fc09473845c163/docs/framework/TOOL-CATALOG-001.md) to select currently available tools. Record applicable gates, their results, and evidence in `reviews/`; a score alone never passes a required gate.

## Artifact identities

This project uses the `FLAGLITE` prefix for stable artifact IDs. Do not reuse IDs. Keep gate results separate from artifact lifecycle statuses, and link decisions/reviews to the exact versions they affect.

## Framework checks

The generated SDD workflow validates artifact metadata, framework snapshot integrity, handoffs, and the app-owned `.sdd/required-checks.json` manifest. Configure that manifest from the approved verification plan before implementation: each check names its task and acceptance criteria, platform/path scope, exact command or manual procedure, pass condition, and evidence location. Required CI commands run on pushes and pull requests; each attempt records the tested SHA, provider run/attempt, event/ref, runtime probe, command exit, and output digests in an uploaded evidence artifact. The workflow has read-only repository permissions, injects no secrets, and does not deploy. Pull-request commands execute untrusted checkout code and must never depend on privileged credentials. CI evidence does not prove semantic correctness or branch protection; require the relevant status checks in repository settings before treating them as merge or release controls.

## Supporting records as needed

Create decision and review records when a decision or gate requires one; add architecture, delivery, and operations records when the lifecycle reaches those stages. The template source provides detailed record templates. This starter does not create empty lifecycle folders or imply that those gates have run.

The SDD `design.md` is canonical. The Impeccable `document` command writes `DESIGN.md` in its project root; on case-insensitive file systems this can collide with `design.md`. Run that command only in an isolated staging copy/worktree, review its output, then place the generated file under `.impeccable/generated/`. Never run it at this repository root.
