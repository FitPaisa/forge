<!-- SPDX-License-Identifier: Apache-2.0 -->
# Plan, build, and maintain

Read this reference when turning a requirement into milestones, executing a planned change, or reconciling affected Forge records.

## Select the working context

Start from the existing entry point, its small set of global constraints, and the active requirement or milestone index. Select the relevant topic and component entries, acceptance records, scoped constraints, and current source. Search headings or metadata before opening a large document. Reuse unchanged content already present in the session. Do not load every milestone, decision, or historical record.

The helper returns compact references rather than injecting whole documents:

```sh
python3 <skill-dir>/scripts/forge.py find authentication --project <project-dir>
python3 <skill-dir>/scripts/forge.py impact topic.authentication --project <project-dir>
```

Its findings guide reading. Follow relevant links and source evidence where catalog coverage or metadata is incomplete.

When resuming one milestone, requirement and acceptance summaries provide context without triggering every sibling milestone. Follow needed topic, dependency and constraint links. For truncated helper output, refine the target or increase `--limit` before considering the selection complete.

## Plan before implementing a new requirement

1. Record the requested outcome, source, boundaries, and affected topics in a requirement record. Resolve consequential uncertainty using the available project context or the user.
2. Inspect applicable constraints, meaningful dependencies, current implementation, and reusable capability candidates. Search relevant source when the catalog lacks a match. Choose reuse, extension, or new implementation based on suitability, and record the material reason.
3. Break the requirement into contextual milestones before implementation. A small requirement can have one milestone. Each milestone references its requirements, topics, dependencies, and separate acceptance records. Group work around a verifiable delivery outcome; a milestone can involve multiple features.
4. Define observable acceptance criteria separately. Reference the affected criteria by stable ID and select checks proportional to the change. Include dependency or constraint checks when their contracts are affected.

Continue an existing plan when the request belongs to it. Reconcile scope changes and their acceptance implications instead of creating competing plans. Planning does not itself authorize publication, deployment, unrelated changes, or a deviation from an explicit instruction.

## Check impact and execute

Before changing a shared capability, inspect its known dependents and applicable constraints. Follow dependencies further where the change crosses another contract boundary. Search current source for consumers when references are partial, stale, or absent. Select the affected acceptance and regression checks; there is no need to load unrelated project history.

Inspect reuse candidates in current source, including their constraints and side effects. Preserve a useful existing abstraction; introduce a new one when the requirement warrants it. A catalog entry alone does not establish suitability, and a missing entry does not establish absence.

Track the active milestone's meaningful state changes, blocker, and next action. Keep temporary reasoning, raw transcripts, and repeated progress narration out of durable records. Concurrent workers should own separate task records and report shared changes to one coordinator; avoid several agents rewriting the same index.

If implementation conflicts with an explicit constraint, record the discrepancy and its impact. Correct the work or obtain the necessary authorization before treating a departure as accepted. Link any authorized deviation to the affected constraint and milestone.

## Verify and update once

Judge completion using the separate acceptance criteria and current implementation evidence. Record what ran and its result; mark unverified or blocked work accurately. Do not infer successful verification from generated code or an agent's confidence.

After a meaningful change, update only affected topics, capabilities, routes, decisions, considerations, deviations, and milestone state. Keep canonical records current and indexes compact. Archive completed detail when it no longer belongs on the active reading path.

Run the structural check when records or links changed:

```sh
python3 <skill-dir>/scripts/forge.py check --project <project-dir>
```

Resolve errors and investigate relevant warnings. Structural validation complements behavioral evidence. During later reconciliation, preserve current source facts and approved intent separately, report contradictions, and refresh only the context that new evidence affects.
