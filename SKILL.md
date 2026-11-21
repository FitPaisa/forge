---
name: fitpaisa-forge
description: >-
  Keep development projects understandable across sessions with small context files in a forge/ subfolder. Start fresh projects or adopt existing codebases and documentation; plan every new requirement into tracked milestones; keep acceptance criteria separate; preserve user constraints, decisions and deviations; discover reusable frontend/backend capabilities; map pages and routes; check dependency impact; and update only affected records. Use when setting up Forge or planning, building, resuming or maintaining a project that already uses it. Quick start: ask $fitpaisa-forge to start a project, adopt a codebase, plan a requirement or resume a milestone. Apache-2.0 licensed; redistribution retains required license/notices.
license: Apache-2.0
metadata:
  version: "1.0.1"
---

# FitPaisa Forge

Give a development agent the smallest reliable project context needed to plan, reuse, build and continue work. Store Forge-managed project knowledge in the repository's `forge/` subfolder, separate from this reusable skill. Support empty project folders and existing codebases. Existing documentation can remain in place and be referenced as evidence; no pre-existing documentation folder is required.

## Quick use

- **Start fresh:** “Use $fitpaisa-forge to start a new project in this folder. The idea is [project description]. Create forge/, capture my requirements and plan the first milestones before implementation.”
- **Adopt:** “Use $fitpaisa-forge to adopt this codebase into forge/, using its existing documentation where relevant.”
- **Plan:** “Use $fitpaisa-forge to plan passwordless authentication into milestones.”
- **Build/resume:** “Use $fitpaisa-forge to continue the client-onboarding milestone.”
- **Refresh/check:** “Use $fitpaisa-forge to check dependency impact and refresh context affected by these changes.”

Use natural-language modes; these are prompts, not installed slash commands. Do not introduce Forge into unrelated work solely because this skill is available.

## Find and load context

1. Follow any existing project instructions. Use `forge/` as the default context root for both fresh and existing projects. Honor an explicitly selected custom root or an already configured Forge installation; never infer a custom root merely because a documentation folder exists. Ask only when genuinely competing configured roots cannot be distinguished.
2. Read the compact entrypoint, the small active global constraints and the index relevant to the task. Then read only the selected requirement/milestone, applicable acceptance criteria, scoped constraints, needed topic/component/page records and decision rationale.
3. Use compact `find` and `impact` output or targeted searches to select files. Refine truncated results or raise the helper's limit before concluding a selection is complete. Indexes route to details; milestones reference canonical topics. Do not recursively read the context folder, reload unchanged context, or pull completed milestone histories into ordinary work.
4. Expand the read set when a dependency, discrepancy or missing fact requires it. Context economy must preserve applicable explicit instructions and sufficient evidence.

For fresh setup or first adoption, read the relevant section of [adoption.md](references/adoption.md). When creating or changing record structure, read the relevant contract in [records.md](references/records.md). For milestone planning, execution, impact review and upkeep, read [lifecycle.md](references/lifecycle.md). Load only references needed for the selected mode.

## Required project behavior

- **Plan before implementation.** Every new requirement gets an outcome, scope and milestone breakdown. Small requirements may have one milestone. Resume or revise existing plans. A milestone can deliver several features; a feature can span milestones. Cross-reference their canonical records.
- **Separate acceptance.** Maintain observable criteria in independent, topic-named files with stable criterion IDs. Milestones reference the applicable criteria. Split large sets by capability or milestone. Do not weaken criteria to mark work complete.
- **Reuse before build.** Inspect relevant frontend patterns/components and backend capabilities. Check current source and contracts. Partial catalogs require targeted source searches. Choose reuse, extension or new implementation based on fit, recording consequential choices.
- **Check impact.** Inspect known dependencies, consumers and applicable constraints. Expand where changed contracts propagate. Derive reverse relationships from canonical direct links. Missing links never prove isolation; related requirement summaries must not trigger loading every sibling milestone.
- **Preserve instructions.** Store original user wording, source, scope and active/superseded state separately. Load global constraints and applicable scoped rules. Distinguish observed behavior, accepted intent, inference and unknowns. Agent decisions cannot authorize changing user instructions.
- **Track departures.** Record conflicts as unresolved deviations. Exceptions need existing or new authorization before implementation. Reference the affected constraint, reason, scope, authorization, state and temporary expiry/revisit condition. Preserve supersession history.
- **Preserve project knowledge.** Record architecture, product/design decisions and rationale; constraints, assumptions, risks, dependencies, non-goals and questions. Page maps include purpose, routes, permissions and sources. Distinguish UI routes from API contracts; reference existing design/API documentation.
- **Verify and maintain.** Track milestone state, blockers, next action and completion evidence against separate acceptance criteria. Record checks that could not run. Update affected records and indexes once after meaningful changes. Keep history discoverable without default loading; avoid diaries and no-op updates.

## Lightweight helper

Python 3.10+; standard library only. Resolve `scripts/forge.py` relative to this installed skill; run against the actual project. The helper validates structure and links, not application correctness or authorization authenticity.

```sh
python3 /path/to/fitpaisa-forge/scripts/forge.py init --project /path/to/project --dry-run
python3 /path/to/fitpaisa-forge/scripts/forge.py init --project /path/to/project
python3 /path/to/fitpaisa-forge/scripts/forge.py find authentication --project /path/to/project
python3 /path/to/fitpaisa-forge/scripts/forge.py impact topic.authentication --project /path/to/project
python3 /path/to/fitpaisa-forge/scripts/forge.py check --project /path/to/project
```

With no configured root, initialization creates `forge/forge.json` and `forge/index.md`, even in an empty project directory. It preserves existing files. The helper does not inspect the application, invent knowledge or install agent instructions; the agent supplies the project context and plan. During authorized setup, add a concise Forge pointer to the existing agent entrypoint, or create a small `AGENTS.md` if none exists. Preserve existing instructions. No external service, vector database, background process or agent-specific runtime is required.

## Scope and delivery

Follow existing project execution and permission boundaries; Forge adds no mandatory approval ceremony, publication, commit or deployment step. When writers overlap, use the project's concurrency convention and give one integrator ownership of shared indexes. Keep confidential project context out of the public skill package. Treat token savings as a hypothesis: evaluate context reads plus maintenance, successful reuse and correctness on representative tasks.

## License

Apache License 2.0; see [LICENSE](LICENSE). Commercial use, modification and redistribution are permitted under its terms. Preserve required license and notices and identify modifications when distributing modified files. No product UI credit line is imposed by this skill. This license does not change the license of a project using Forge or its existing materials.
