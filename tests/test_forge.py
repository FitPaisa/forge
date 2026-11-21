# SPDX-License-Identifier: Apache-2.0
"""Behavioral tests for the offline Forge helper. No project files are touched."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "forge.py"
SPEC = importlib.util.spec_from_file_location("forge_helper", SCRIPT)
forge = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = forge
SPEC.loader.exec_module(forge)


class ForgeHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fitpaisa-forge-test-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.root = self.project / "project-docs"
        forge.init(self.project, self.root, False)

    def record(self, filename, record_id, kind="topic", **metadata):
        data = {"id": record_id, "type": kind, "title": record_id, "status": "active"}
        data.update(metadata)
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        header = "\n".join(f"{key}: {json.dumps(value)}" for key, value in data.items())
        path.write_text(f"---\n{header}\n---\n\n# {record_id}\n", encoding="utf-8")
        return path

    def loaded(self):
        return forge.load_records(self.root)

    def checked(self):
        records, errors = self.loaded()
        return forge.check(self.project, self.root, records, errors)

    def impact_ids(self, *targets):
        records, errors = self.loaded()
        self.assertEqual(errors, [])
        result = forge.impact(self.project, self.root, records, list(targets), 100)
        return {record["id"] for record in result["records"]}

    def test_init_preserves_existing_documents_and_is_idempotent(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = forge.init(self.project, self.root, False)
        self.assertEqual(result["created"], [])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        unconfigured = self.project / "legacy"
        unconfigured.mkdir()
        entry = unconfigured / "index.md"
        entry.write_text("Existing human-authored context\n", encoding="utf-8")
        adopted = forge.init(self.project, unconfigured, False)
        self.assertEqual(adopted["created"], ["forge.json"])
        self.assertEqual(entry.read_text(), "Existing human-authored context\n")

    def test_dry_run_creates_nothing(self):
        absent = self.project / "new-context"
        result = forge.init(self.project, absent, True)
        self.assertEqual(result["would_create"], ["forge.json", "index.md"])
        self.assertFalse(absent.exists())

    def test_cli_initializes_fresh_project_in_forge_without_existing_context(self):
        fresh = self.project / "fresh-project"
        fresh.mkdir()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "init", "--project", str(fresh)],
            check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["root"], "forge")
        self.assertEqual(set(output["created"]), {"forge.json", "index.md"})
        self.assertEqual({p.name for p in fresh.iterdir()}, {"forge"})
        self.assertTrue((fresh / "forge" / "index.md").is_file())
        self.assertEqual(json.loads((fresh / "forge" / "forge.json").read_text()),
                         {"schema_version": 1, "entrypoint": "index.md"})
        check = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--project", str(fresh)],
            check=False, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr or check.stdout)
        self.assertEqual(json.loads(check.stdout)["root"], "forge")

    def test_cli_default_forge_preserves_unconfigured_project_docs(self):
        existing = self.project / "existing-project"
        project_docs = existing / "project-docs"
        project_docs.mkdir(parents=True)
        original = {
            "architecture.md": b"# Existing architecture\nThis is maintained by the project owner.\n",
            "index.md": b"# Project documentation\n[Architecture](architecture.md)\n",
        }
        for name, content in original.items():
            (project_docs / name).write_bytes(content)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "init", "--project", str(existing)],
            check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout)["root"], "forge")
        self.assertEqual(original, {p.name: p.read_bytes() for p in project_docs.iterdir()})
        self.assertFalse((project_docs / "forge.json").exists())
        self.assertTrue((existing / "forge" / "index.md").is_file())
        self.assertTrue((existing / "forge" / "forge.json").is_file())

    def test_cli_explicit_custom_root_remains_supported_and_detected(self):
        existing = self.project / "explicit-context-project"
        project_docs = existing / "project-docs"
        project_docs.mkdir(parents=True)
        legacy = project_docs / "notes.md"
        legacy.write_bytes(b"# Existing project notes\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "init", "--project", str(existing), "--root", "project-docs"],
            check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout)["root"], "project-docs")
        self.assertEqual(legacy.read_bytes(), b"# Existing project notes\n")
        self.assertFalse((existing / "forge").exists())
        check = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--project", str(existing)],
            check=False, capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr or check.stdout)
        self.assertEqual(json.loads(check.stdout)["root"], "project-docs")

    def test_root_detection_requires_choice_when_ambiguous(self):
        self.assertEqual(forge.resolve_root(self.project, None), self.root)
        forge.init(self.project, self.project / "forge", False)
        with self.assertRaisesRegex(forge.ForgeError, "Multiple Forge roots"):
            forge.resolve_root(self.project, None)
        self.assertEqual(forge.resolve_root(self.project, "project-docs"), self.root)

    def test_root_and_entrypoint_cannot_escape_or_follow_symlinks(self):
        for value in ("../outside", str(self.project / "absolute"), "."):
            with self.assertRaises(forge.ForgeError):
                forge.resolve_root(self.project, value, initialize=True)
        outside = self.project.parent / (self.project.name + "-outside")
        self.root.joinpath("escape").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(forge.ForgeError, "Symlink"):
            forge.resolve_root(self.project, "project-docs/escape", initialize=True)
        config = self.root / "forge.json"
        config.write_text(json.dumps({"schema_version": 1, "entrypoint": "../victim.md"}))
        with self.assertRaises(forge.ForgeError):
            forge.init(self.project, self.root, False)
        self.assertFalse((self.project / "victim.md").exists())

    def test_invalid_metadata_and_duplicate_ids_are_reported(self):
        self.record("a.md", "topic.auth", status="invented")
        self.record("b.md", "topic.auth")
        self.root.joinpath("bad.md").write_text(
            "---\nid: topic.bad\ntype: topic\ntitle: Bad\nstatus: active\ndepends_on: [broken\n---\n")
        report = self.checked()
        self.assertFalse(report["ok"])
        joined = "\n".join(report["errors"])
        self.assertIn("Duplicate ID", joined)
        self.assertIn("unknown status", joined)
        self.assertIn("inline JSON", joined)

    def test_separate_acceptance_and_dangling_ids_are_checked(self):
        self.record("topic.md", "topic.auth")
        self.record("milestone.md", "milestone.login", "milestone",
                    status="planned", acceptance=["topic.auth"], topics=["topic.missing"])
        self.record("empty.md", "milestone.empty", "milestone", status="planned")
        report = self.checked()
        joined = "\n".join(report["errors"])
        self.assertIn("not a separate acceptance record", joined)
        self.assertIn("missing ID 'topic.missing'", joined)
        self.assertIn("milestone needs separate acceptance", joined)
        self.record("acceptance.md", "acceptance.login", "acceptance")
        self.record("milestone.md", "milestone.login", "milestone",
                    status="planned", acceptance=["acceptance.login"], topics=["topic.auth"])
        (self.root / "empty.md").unlink()
        self.assertTrue(self.checked()["ok"])

    def test_milestone_can_link_multiple_features_and_features_multiple_milestones(self):
        self.record("auth.md", "topic.auth")
        self.record("profile.md", "topic.profile")
        self.record("acceptance.md", "acceptance.onboarding", "acceptance")
        self.record("m1.md", "milestone.onboarding", "milestone", status="planned",
                    topics=["topic.auth", "topic.profile"], acceptance=["acceptance.onboarding"])
        self.record("m2.md", "milestone.roles", "milestone", status="planned",
                    topics=["topic.auth"], acceptance=["acceptance.onboarding"])
        self.assertTrue(self.checked()["ok"])
        ids = self.impact_ids("topic.auth")
        self.assertTrue({"milestone.onboarding", "milestone.roles"}.issubset(ids))

    def test_reverse_dependency_closure_is_transitive_and_cycle_safe(self):
        self.record("auth.md", "topic.auth", depends_on=["topic.sessions"])
        self.record("sessions.md", "topic.sessions", depends_on=["topic.auth"])
        self.record("onboard.md", "topic.onboard", depends_on=["topic.auth"])
        self.record("admin.md", "topic.admin", depends_on=["topic.onboard"])
        self.record("unrelated.md", "topic.unrelated")
        self.assertEqual(self.impact_ids("topic.auth"),
                         {"topic.auth", "topic.sessions", "topic.onboard", "topic.admin"})

    def test_global_scoped_and_linked_constraints_and_deviations_are_routed(self):
        (self.project / "src").mkdir()
        (self.project / "src" / "auth.ts").write_text("export const auth = true;\n")
        self.record("auth.md", "topic.auth", sources=["src/auth.ts"],
                    constraints=["constraint.auth"])
        self.record("global.md", "constraint.global", "constraint", scope=["global"], source="User: global rule")
        self.record("design.md", "constraint.design", "constraint", scope=["src/**"], source="User: design rule")
        self.record("auth-rule.md", "constraint.auth", "constraint", scope=["server/**"], source="User: auth rule")
        self.record("other.md", "constraint.other", "constraint", scope=["docs/**"], source="User: docs rule")
        self.record("deviation.md", "deviation.design", "deviation", status="observed",
                    constraints=["constraint.design"])
        self.assertEqual(self.impact_ids("src/auth.ts"),
                         {"topic.auth", "constraint.global", "constraint.design", "constraint.auth", "deviation.design"})

    def test_new_unknown_source_still_gets_scoped_constraints(self):
        self.record("design.md", "constraint.design", "constraint", scope=["src/**"], source="User rule")
        self.assertIn("constraint.design", self.impact_ids("src/new-page.ts"))

    def test_changed_constraint_routes_explicit_and_scoped_consumers_then_dependents(self):
        self.record("design.md", "constraint.design", "constraint", scope=["src/ui/**"], source="User rule")
        self.record("explicit.md", "topic.explicit", constraints=["constraint.design"])
        self.record("scoped.md", "topic.scoped", sources=["src/ui/form.tsx"])
        self.record("dependent.md", "topic.dependent", depends_on=["topic.scoped"])
        self.record("unrelated.md", "topic.unrelated", sources=["server/job.py"])
        ids = self.impact_ids("constraint.design")
        self.assertTrue({"constraint.design", "topic.explicit", "topic.scoped", "topic.dependent"}.issubset(ids))
        self.assertNotIn("topic.unrelated", ids)

    def test_milestone_context_loads_nested_topic_constraints_and_source_scopes(self):
        self.record("design.md", "constraint.design", "constraint", scope=["src/**"], source="User design rule")
        self.record("auth-rule.md", "constraint.auth", "constraint", scope=["server/**"], source="User auth rule")
        self.record("auth.md", "topic.auth", sources=["src/auth.ts"], constraints=["constraint.auth"])
        self.record("acceptance.md", "acceptance.login", "acceptance")
        self.record("m1.md", "milestone.login", "milestone", status="planned",
                    topics=["topic.auth"], acceptance=["acceptance.login"])
        ids = self.impact_ids("milestone.login")
        self.assertTrue({"milestone.login", "topic.auth", "acceptance.login",
                         "constraint.auth", "constraint.design"}.issubset(ids))

    def test_loading_shared_context_does_not_expand_all_reverse_consumers(self):
        self.record("forms.md", "component.forms", "component")
        self.record("auth.md", "topic.auth", depends_on=["component.forms"])
        self.record("profile.md", "topic.profile", depends_on=["component.forms"])
        self.record("acceptance.md", "acceptance.auth", "acceptance")
        self.record("m1.md", "milestone.auth", "milestone", status="planned",
                    topics=["topic.auth"], acceptance=["acceptance.auth"])
        ids = self.impact_ids("milestone.auth")
        self.assertIn("component.forms", ids)
        self.assertNotIn("topic.profile", ids)

    def test_shared_requirement_and_acceptance_are_leaves_without_sibling_milestones(self):
        self.record("design.md", "constraint.design", "constraint", scope=["src/**"], source="User design rule")
        self.record("auth-rule.md", "constraint.auth", "constraint", scope=["server/**"], source="User auth rule")
        self.record("auth.md", "topic.auth", constraints=["constraint.auth"], sources=["src/auth.ts"])
        self.record("unrelated.md", "topic.unrelated")
        self.record("requirement.md", "requirement.account", "requirement",
                    topics=["topic.auth", "topic.unrelated"],
                    milestones=["milestone.login", "milestone.profile", "milestone.preferences"])
        self.record("acceptance.md", "acceptance.account", "acceptance",
                    milestones=["milestone.login", "milestone.profile", "milestone.preferences"])
        self.record("login.md", "milestone.login", "milestone", status="planned",
                    topics=["topic.auth"], requirements=["requirement.account"], acceptance=["acceptance.account"])
        self.record("profile.md", "milestone.profile", "milestone", status="planned",
                    topics=["topic.unrelated"], requirements=["requirement.account"], acceptance=["acceptance.account"])
        self.record("preferences.md", "milestone.preferences", "milestone", status="planned",
                    topics=["topic.unrelated"], requirements=["requirement.account"], acceptance=["acceptance.account"])
        ids = self.impact_ids("milestone.login")
        self.assertTrue({"milestone.login", "topic.auth", "requirement.account", "acceptance.account",
                         "constraint.auth", "constraint.design"}.issubset(ids))
        self.assertFalse({"milestone.profile", "milestone.preferences", "topic.unrelated"}.intersection(ids))

    def test_deviation_needs_constraint_and_authorization_when_accepted(self):
        self.record("rule.md", "constraint.design", "constraint", source="User: no shadows", scope=["global"])
        self.record("deviation.md", "deviation.shadow", "deviation", status="approved",
                    constraints=["constraint.design"])
        report = self.checked()
        self.assertIn("authorization", "\n".join(report["errors"]))
        self.record("deviation.md", "deviation.shadow", "deviation", status="approved",
                    constraints=["constraint.design"], authorization="User message 2026-11-21: exception for print preview")
        self.assertTrue(self.checked()["ok"])

    def test_local_sources_links_and_staleness_are_checked_without_network(self):
        (self.project / "src").mkdir()
        (self.project / "src" / "auth.ts").write_text("export {};\n")
        path = self.record("topics/auth.md", "topic.auth", sources=["src/auth.ts#login", "https://example.invalid/spec"],
                           verified_at="2000-01-01")
        with path.open("a") as stream:
            stream.write("[source](../../src/auth.ts)\n[missing](absent.md)\n[remote](https://example.invalid/no-fetch)\n")
        report = self.checked()
        self.assertIn("missing local link", "\n".join(report["errors"]))
        self.assertIn("90 days", "\n".join(report["warnings"]))
        self.assertNotIn("missing source", "\n".join(report["errors"]))

    def test_sources_and_links_cannot_escape_project_or_reference_sensitive_paths(self):
        path = self.record("unsafe.md", "topic.unsafe", sources=["../outside", ".env", ".git/config"])
        with path.open("a") as stream:
            stream.write("[escape](../../outside)\n")
        report = self.checked()
        self.assertFalse(report["ok"])
        self.assertIn("Excluded path", "\n".join(report["errors"]))
        self.assertIn("invalid local link", "\n".join(report["errors"]))

    def test_unrelated_legacy_markdown_is_not_rewritten_or_validated_as_a_record(self):
        legacy = self.root / "legacy.md"
        content = "---\nlayout: default\ncustom:\n  nested: permitted in old docs\n---\n\n[old link](missing-old-link.md)\n"
        legacy.write_text(content)
        self.assertTrue(self.checked()["ok"])
        self.assertEqual(legacy.read_text(), content)

    def test_find_is_compact_metadata_search_and_excludes_history_by_default(self):
        path = self.record("auth.md", "topic.auth", title="Authentication")
        with path.open("a") as stream:
            stream.write("A body-only phrase: invisible-keyword\n")
        self.record("old.md", "topic.auth-old", title="Authentication", status="superseded")
        records, errors = self.loaded()
        self.assertEqual(errors, [])
        self.assertEqual(forge.find(records, "Authentication", 1, False)["total"], 1)
        self.assertEqual(forge.find(records, "Authentication", 1, True)["total"], 2)
        self.assertTrue(forge.find(records, "Authentication", 1, True)["truncated"])
        self.assertEqual(forge.find(records, "invisible-keyword", 5, False)["total"], 0)

    def test_cli_errors_are_json_and_nonzero(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = forge.main(["check", "--project", str(self.project), "--root", "../outside"])
        self.assertEqual(code, 2)
        self.assertIn("error", json.loads(output.getvalue()))


if __name__ == "__main__":
    unittest.main()
