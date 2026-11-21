# FitPaisa Forge

<img src="assets/forge-icon.png" width="144" height="144" alt="FitPaisa Forge: a golden anvil and spark on navy" />

**Small, reliable project context. Planned milestones. Reuse before build.**

FitPaisa Forge is a reusable development skill that keeps a project's working knowledge in a `forge/` subfolder of its repository. An agent finds the context relevant to its task, checks existing capabilities, plans the work, verifies it and maintains affected records. The context survives new sessions and can be shared through normal version control.

It works with empty project folders and existing codebases. No prior documentation folder is required. Setup starts with a compact index and the active work; coverage grows as the project evolves. Existing documentation can stay where it is and be referenced from Forge. New Forge-managed records belong under `forge/`.

## What it does

- Breaks each new requirement into milestones before implementation, with progress, blockers, next actions and completion evidence.
- Keeps acceptance criteria in separate files, referenced by milestones.
- Organizes lasting context by domain or topic, such as authentication, and shared patterns, such as frontend forms.
- Maintains frontend and backend reuse catalogs linked to current source, usage constraints and relevant examples.
- Preserves product, architecture and design decisions, including rationale and supersession.
- Records explicit user instructions separately, with applicability, original wording and source. Tracks unresolved departures and authorized exceptions.
- Maps key pages, route patterns, permissions and source locations, while referring to existing API specifications.
- Records meaningful dependencies and derives consumers for impact checks.
- Preserves project considerations: constraints, assumptions, risks, non-goals and open questions.
- Loads relevant files through compact indexes and updates changed facts instead of writing session diaries.

Milestones and features have a many-to-many relationship. A delivery milestone can include authentication, profiles and forms; authentication may evolve over several milestones. The records reference each other without duplicating their contents.

## Quick start

Install the `fitpaisa-forge` folder in your agent's supported skills directory. For a published GitHub copy, Codex users can ask its skill installer to install the repository's skill folder. The package includes `SKILL.md` and optional Codex UI metadata in `agents/openai.yaml`; other Agent Skills-compatible tools can use the instructions and helper without the UI metadata.

FitPaisa workspace members can install it from **Skills → Shared by FitPaisa**. For a local Codex installation from this repository, ask:

> Use $skill-installer to install the skill at the root of https://github.com/FitPaisa/forge, branch dev, with the installation name fitpaisa-forge.

This repository's root is the skill folder: `SKILL.md`, `agents/`, `assets/`, `references/` and `scripts/` belong together. The installed skill maintains each development project's context in that project's own `forge/` subfolder.

For a fresh project, open or create its project folder and ask:

> Use $fitpaisa-forge to start a new project in this folder. The idea is [describe the project]. Create forge/, record my requirements and design constraints, and plan the first milestones with separate acceptance criteria before implementation.

The agent creates the minimal `forge/` entrypoint, records known goals and constraints, keeps unresolved choices explicit, and plans the first requirement. Components and routes are documented when they exist. Existing code, documentation and Git history are not prerequisites.

For an existing project, ask:

> Use $fitpaisa-forge to adopt this codebase into forge/. Use existing documentation where relevant and start with the work I am doing now.

For later work:

> Use $fitpaisa-forge to plan passwordless authentication into milestones. Keep acceptance criteria separate and check existing capabilities first.

> Use $fitpaisa-forge to resume the current onboarding milestone and check the impact on dependent features.

> Use $fitpaisa-forge to refresh context affected by these changes and report unresolved instruction deviations.

These are natural-language prompts, not special CLI commands. Naming the skill explicitly selects it; automatic discovery depends on the host. A short pointer in the project's existing agent instructions helps future sessions locate the same context. Adoption preserves those existing instructions.

## A project layout

Create records only as they become useful. Keep an established project convention when it already serves the same purpose.

```text
forge/                              # Default for new and existing projects
  forge.json                        # Format version and entrypoint
  index.md                          # Compact reading map and active work
  constraints/design.md             # Explicit user instructions
  considerations/data-retention.md  # Constraints, risks and unknowns
  topics/authentication.md          # Current behavior and dependencies
  components/frontend/forms.md      # Reusable UI capabilities
  components/backend/notifications.md
  pages/account.md                  # Purpose, route and permissions
  requirements/passwordless.md
  milestones/M03-client-onboarding.md
  acceptance/client-onboarding.md   # Separate completion criteria
  decisions/DEC-001-session-storage.md
  deviations/DEV-001-legacy-spacing.md
```

Topic indexes can be introduced when the entrypoint grows. Keep global constraints small; select scoped constraints through topics and paths. Completed milestones and historical decisions remain available on demand.

See [record contracts](references/records.md), [incremental adoption](references/adoption.md) and the [planning/build lifecycle](references/lifecycle.md) for details. Agents should load the reference needed for the current mode, rather than all references.

## Optional helper

Requires **Python 3.10+**, with no extra packages or network access. Run it using the installed skill's path:

```sh
python3 scripts/forge.py init --project /path/to/project --dry-run
python3 scripts/forge.py init --project /path/to/project
python3 scripts/forge.py find authentication --project /path/to/project
python3 scripts/forge.py impact topic.authentication --project /path/to/project
python3 scripts/forge.py check --project /path/to/project
```

- `init` creates a minimal configuration and entrypoint, preserving existing files. It does not analyze application code or adopt a project by itself.
- `find` returns compact matches from record metadata.
- `impact` identifies related constraints and consumers through record links and path scopes.
- `check` checks the structure and local references. Application behavior and the authenticity of recorded authorization still require evidence.

With no configured Forge root, `init` creates `forge/forge.json` and `forge/index.md`. The project directory must exist; it may be empty. A custom root is an optional advanced setting selected explicitly with `--root`, or retained from an existing configured installation. The helper never adopts an unrelated documentation folder merely because it exists. Multiple configured roots require an explicit choice.

## Validation and limitations

Run the helper tests with:

```sh
python3 -m unittest discover -s tests -v
```

Forge supports the agent's investigation; a catalog or dependency map may be incomplete. Reuse needs source inspection, and completion needs applicable acceptance checks. Existing implementation establishes observed behavior; explicit user instructions establish intended constraints. Unexplained discrepancies remain visible.

Token reduction is an objective, not a promised benchmark. Measure context reading and maintenance together, alongside correctness, duplicate implementations, successful reuse and continuity across sessions.

The skill does not run background services, publish work, commit changes or deploy applications. Its license does not change a project's license. Keep project-specific context separate when sharing the generic skill.

## License

**Apache License 2.0** — see [LICENSE](LICENSE).

You may use, modify, distribute and sell the skill, including in commercial and closed-source work, subject to that license. Apache 2.0 includes license/notice preservation and modified-file notice requirements; it is not an attribution-free public-domain dedication. This package imposes no additional product UI credit requirement.

The icon uses FitPaisa navy `#173B72` and yellow `#F9D758`. The bundled icon is included with this package under the same license.
