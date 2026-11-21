<!-- SPDX-License-Identifier: Apache-2.0 -->
# Record contracts

Read the relevant record contract when creating or materially updating that kind of context. Create records as facts and work require them; the list below is not a scaffold to generate in full.

## Files and metadata

Use descriptive feature or topic filenames and stable IDs. Keep topics, requirements, milestones, and acceptance records as peers: a milestone can contain several features, and a feature can span milestones. References express these relationships without copying content.

Managed Markdown records start with a flat YAML subset:

```yaml
---
id: milestone.client-onboarding
type: milestone
title: Client onboarding
status: planned
topics: ["topic.authentication", "topic.profiles"]
requirements: ["requirement.client-onboarding"]
acceptance: ["acceptance.client-onboarding"]
depends_on: ["milestone.account-foundation"]
sources: ["src/onboarding/index.ts"]
---
```

Required fields are `id`, `type`, `title`, and `status` strings. Reference arrays use inline JSON arrays of strings. Supported arrays are `depends_on`, `constraints`, `topics`, `requirements`, `acceptance`, `milestones`, `sources`, and `scope`. Optional strings include `source`, `authorization`, `verified_at`, and `coverage`. Additional flat string fields can capture facts such as `knowledge: inferred`. Nested metadata is unsupported. Keep substantive explanation in Markdown.

Constraint records additionally require `source` and nonempty `scope` metadata. Approved or applied deviations require `authorization` and affected `constraints`. Milestone `acceptance` arrays contain acceptance-record IDs only; put individual criterion IDs and links in the milestone body.

`sources` are existing project-relative evidence paths, not paths relative to the Forge folder. Describe planned files in the body until they exist. Use `scope` for project-relative path globs; `scope: ["global"]` marks a global constraint. Keep external sources as ordinary links or a `source` reference; the helper does not fetch them. Existing external documents can remain unchanged and be linked from managed records.

Each fact has one canonical home. Indexes contain short relevance summaries and links; full rationale, rules, code, and acceptance text stay in their owning files. Split a record when different tasks need independent parts, rather than at an arbitrary file count.

## Record contents

| Type | Essential content |
| --- | --- |
| `index` | Purpose of this area; compact ID, summary, status, and location entries; when to read each entry. |
| `topic` | Current behavior, boundaries, relevant contracts, dependencies, implementation sources, known gaps, and last verification. |
| `component` | Reusable frontend or backend capability, source symbol/path, intended use, example reference, constraints, active/deprecated status, and usage recommendation. |
| `requirement` | Requested outcome, scope and exclusions, source, affected topics, and references to delivery milestones and separate acceptance records. |
| `milestone` | Delivery outcome, requirement/topic references, dependencies, work and reuse choices, status, blocker, next action, and completion evidence. An acceptance reference is required. |
| `acceptance` | Independently maintained criterion IDs, observable outcomes, verification approach, requirement/milestone references, and actual results or evidence. |
| `constraint` | Explicit user instruction, original wording, source/date, applicability, status, and a practical compliance check where possible. |
| `decision` | Choice, rationale, alternatives considered, source/authorization where relevant, affected topics, and any superseded decision. |
| `deviation` | Affected constraint IDs, reason, scope, authorization evidence, implementation state, and expiry or review condition when temporary. |
| `consideration` | Applicable architectural, product, operational, accessibility, performance, security, or domain consideration; distinguish a fact, assumption, risk, and open question. |
| `page` | Page purpose, route pattern, source, permissions, implementation status, and relevant topic/component references. |

Frontend capabilities can include shared components, tokens, layout and interaction patterns, and Storybook references. Backend capabilities can include services, validation, authorization, persistence helpers, jobs, and integrations. Record contracts and meaningful side effects; keep implementations in source.

Page maps should distinguish UI routes from API endpoints. Store route patterns such as `/accounts/:id`, with deployment bases linked separately when useful. Reference existing router and API specifications instead of maintaining another complete API description.

Use milestone states `planned`, `in_progress`, `blocked`, and `completed`; acceptance states `draft`, `active`, and `verified`; constraint states `active` and `superseded`; decision states `proposed`, `accepted`, and `superseded`. Deviations can be `observed`, `proposed`, `approved`, `applied`, `resolved`, or `rejected`. Topics, components, considerations, and pages normally use `active` or `deprecated`. Use `partial`, `inferred`, or `unverified` where the state needs explicit qualification, with the explanation in the body.

## Constraints, decisions, and deviations

Keep explicit instructions independent of inferred conventions and ordinary decisions. A small set of global rules belongs on the entry reading path. Scoped rules are discoverable through topic references and path globs. Retain original wording alongside any operational interpretation. A clarification or superseding user instruction needs a traceable source.

A decision record cannot grant permission to breach a constraint. A deviation in `approved` or `applied` state must reference its affected constraints and nonempty authorization evidence. Authorization must actually exist in the user request or another authoritative source; an agent-written assertion is insufficient. An observed mismatch remains unresolved until corrected or authorized. Preserve its history after resolution.

Acceptance records remain separate from milestone work plans and user constraints. Do not weaken criteria to match the implementation. Amend them when the requirement changes, preserving the reason and source of that change. Group small related criteria together; split large sets by capability or milestone.

## Dependency and freshness references

Declare meaningful dependencies in one direction with `depends_on`. Derive reverse references instead of manually maintaining a second list. Use the relationship arrays for affected topics, requirements, acceptance, and constraints. Reference concrete source and test paths so an impact investigation can reach the implementation.

Set `verified_at` only after actual checking, and describe partial coverage precisely. Staleness or a broken link is a reason to inspect current evidence. Passing structural checks does not establish correct behavior, complete coverage, or genuine authorization.
