<!-- SPDX-License-Identifier: Apache-2.0 -->
# Adopt a new or existing project

Read the relevant section when starting a fresh project or adopting an existing codebase. Forge-managed records belong in `forge/` by default. No existing code or documentation folder is required. Setup produces a useful starting point for the current work; it does not require a complete repository inventory.

## Start a fresh project

1. Work in the user's intended project directory; create it if the requested setup includes creating the folder. An empty directory is sufficient. Use `forge/` unless the user explicitly selects another root.
2. Create the minimal entrypoint and configuration using `init`, then record the user's project description, requested outcomes, explicit design/technical constraints and known considerations. Create only records with useful content. Keep missing information as open questions; ask for consequential choices when needed rather than inventing requirements, technology choices or historical decisions.
3. Plan the first requirement into one or more contextual milestone files. Keep acceptance criteria in separate files and link them. A project without existing components has no reuse candidates yet; document actual capabilities and routes as implementation creates them.
4. Add a short pointer to `forge/index.md` in the project's agent instructions, creating a small `AGENTS.md` when none exists. Proceed with the authorized milestone work. Git initialization, commits and publication are not required by Forge.

## Find the existing context

1. Identify the project root and read any existing agent instructions. Inspect filenames and short indexes for architecture documents, design rules, plans, component documentation, API specifications, routes and tests, wherever they live.
2. Use `forge/` for the new Forge records. Preserve existing canonical documentation and link it as source evidence without moving, copying or rewriting it. Retain a custom root only when explicitly selected or already configured for Forge.
3. If several configured Forge roots exist and none is designated, ask which to use before initializing. Unconfigured documentation directories are source material, not competing Forge roots. Do not merge roots or select one by modification time. Resolve different services independently when the repository already has separate ownership or context boundaries.
4. Read enough source to understand the active requirement and its likely reusable capabilities. Inspect relevant manifests, entry points, routes, component exports, and focused tests. Skip generated files, dependencies, binaries, secret files, and unrelated implementation areas.

The helper can create the minimal scaffold:

```sh
python3 <skill-dir>/scripts/forge.py init --project <project-dir> --dry-run
python3 <skill-dir>/scripts/forge.py init --project <project-dir>
```

Use the preview to identify the exact files. Without a configured root, initialization creates `forge/forge.json` and `forge/index.md`; the agent supplies grounded project content. Keep the chosen root within the project. Existing files remain user-owned.

## Seed the smallest useful baseline

Populate the entry point with the project purpose, active work, a short list of global constraints, and a reading map. Add links to existing documents and the topic, component, milestone, and acceptance records required for the current task. Create additional files only when they contain useful facts.

Use topic names for durable knowledge, such as `topics/authentication.md`; keep reusable patterns in the appropriate component catalog, such as `components/frontend/forms.md`. Milestones group delivery work across those topics and reference independent acceptance records.

When authorized to adopt the repository, add a concise pointer to the Forge entry point in its existing agent instruction file. Preserve all surrounding instructions. Tool-specific entry files should point to the same context instead of duplicating its rules. Initialization itself does not edit agent instructions.

## Classify what is known

- **Observed:** source or executable evidence establishes current behavior. Include project-relative source paths and the date actually checked.
- **Documented intent:** a user instruction, approved decision, or existing authoritative specification establishes what should be true. Preserve its source and scope.
- **Inferred:** a pattern appears likely from inspected implementation. Label it as inference and cite the inspected source; it is not an approved requirement.
- **Unknown:** evidence is absent, ambiguous, or contradictory. Record the question without filling it with a plausible answer.

Current source establishes implementation facts. User requirements and accepted decisions establish intended behavior. Report discrepancies between them; do not silently change either source of truth. Record an existing breach of an explicit instruction as an unresolved deviation, not a retroactively approved exception.

## Continue incrementally

Seed current requirements and milestones from real user requests and existing plans. Record historical completion or rationale only when evidence supports it. Mark initial catalogs and maps as partial, with their covered topics or paths identified. A missing entry is a discovery prompt, not proof that a capability does not exist.

After the baseline exists, continue with normal planning and execution. Expand Forge coverage when work reaches a new topic, exposes a durable constraint, or changes a shared contract. Keep existing documentation in place; use links and small routing records to make it discoverable.
