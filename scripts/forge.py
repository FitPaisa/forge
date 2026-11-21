#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Small, offline discovery and consistency helpers for FitPaisa Forge.

Only Forge record headers are indexed. Source code is never executed or read.
The metadata parser intentionally supports a flat YAML subset: scalar strings
and inline JSON arrays of strings. No YAML dependency or tag evaluation is used.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from datetime import date
import fnmatch
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit


TYPES = {"index", "topic", "component", "requirement", "milestone", "acceptance",
         "constraint", "decision", "deviation", "consideration", "page"}
STATUSES = {"active", "draft", "planned", "not_started", "in_progress", "in-progress",
            "blocked", "completed", "complete", "verified", "accepted", "superseded",
            "deprecated", "proposed", "approved", "applied", "resolved", "rejected",
            "observed", "open", "partial", "inferred", "confirmed", "unverified", "archived"}
HISTORY = {"superseded", "deprecated", "archived", "rejected"}
REF_FIELDS = {"depends_on", "constraints", "topics", "requirements", "acceptance", "milestones"}
ARRAY_FIELDS = REF_FIELDS | {"sources", "scope"}
DENIED_DIRS = {".git", ".hg", ".svn", "node_modules", "vendor", ".venv", "venv",
               ".aws", ".ssh", "__pycache__", "secrets"}
SECRET_NAMES = {"credentials.json", "credentials", "id_rsa", "id_ed25519"}
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\((<[^>]*>|[^\s)]*)(?:\s+[\"'][^)]*)?\)")
MAX_RECORD_BYTES = 512 * 1024


class ForgeError(ValueError):
    pass


def denied(parts: tuple[str, ...]) -> bool:
    return any(p in DENIED_DIRS or p in SECRET_NAMES or p.startswith(".env") for p in parts)


def within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def safe_path(base: Path, value: str, *, allow_glob: bool = False) -> Path:
    """Validate lexical and resolved containment before touching a path."""
    candidate = Path(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ForgeError(f"Expected a project-relative path without '..': {value!r}")
    if denied(candidate.parts):
        raise ForgeError(f"Excluded path: {value!r}")
    cursor = base
    for part in candidate.parts:
        if allow_glob and any(c in part for c in "*?["):
            break
        cursor = cursor / part
        if cursor.is_symlink():
            raise ForgeError(f"Symlink references are not indexed: {value!r}")
    resolved = (base / candidate).resolve()
    if not within(resolved, base):
        raise ForgeError(f"Path leaves its allowed root: {value!r}")
    return resolved


def project_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ForgeError(f"Project directory does not exist: {path}")
    return path


def read_config(root: Path) -> dict:
    config_path = safe_path(root, "forge.json")
    if not config_path.is_file():
        raise ForgeError(f"No forge.json in {root}; use init to establish this root.")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ForgeError(f"Invalid forge.json: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ForgeError("forge.json must be an object with schema_version: 1.")
    entrypoint = data.get("entrypoint")
    if not isinstance(entrypoint, str):
        raise ForgeError("forge.json entrypoint must be a relative Markdown path.")
    entry = safe_path(root, entrypoint)
    if entry.suffix.lower() != ".md":
        raise ForgeError("forge.json entrypoint must name a Markdown file.")
    return data


def resolve_root(project: Path, root_arg: str | None, *, initialize: bool = False) -> Path:
    if root_arg:
        root = safe_path(project, root_arg)
        if root == project:
            raise ForgeError("Use a context subfolder, not the project root itself.")
        return root
    roots = []
    for item in sorted(project.iterdir()):
        if item.is_symlink() or denied((item.name,)) or not item.is_dir():
            continue
        if (item / "forge.json").exists():
            roots.append(item)
    if len(roots) > 1:
        choices = ", ".join(str(p.relative_to(project)) for p in roots)
        raise ForgeError(f"Multiple Forge roots found ({choices}); choose --root explicitly.")
    if roots:
        return roots[0]
    if initialize:
        return safe_path(project, "forge")
    raise ForgeError("No configured Forge root found. Use init to create forge/, or pass --root only for an explicitly selected custom context folder.")


def parse_header(text: str, label: str) -> dict | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ForgeError(f"{label}: unclosed metadata header.")
    # Existing documentation without a Forge ID is outside this helper's schema.
    if not any(re.match(r"^id\s*:", line) for line in lines[1:end]):
        return None
    metadata: dict = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace() or ":" not in line:
            raise ForgeError(f"{label}: use flat key: value metadata; nested YAML is unsupported.")
        key, raw = line.split(":", 1)
        key, raw = key.strip(), raw.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key in metadata:
            raise ForgeError(f"{label}: invalid or duplicate metadata key {key!r}.")
        if raw.startswith(("[", '"', "{")):
            try:
                value = json.loads(raw)
            except ValueError as exc:
                raise ForgeError(f"{label}: {key} must use valid inline JSON syntax.") from exc
        elif raw.startswith("'") and raw.endswith("'"):
            value = raw[1:-1].replace("''", "'")
        else:
            if raw.startswith(("|", ">", "!", "&", "*")):
                raise ForgeError(f"{label}: unsupported metadata syntax for {key}.")
            value = raw
        if key in ARRAY_FIELDS:
            if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
                raise ForgeError(f"{label}: {key} must be an inline JSON array of nonempty strings.")
        elif not isinstance(value, str):
            raise ForgeError(f"{label}: {key} must be a scalar string.")
        metadata[key] = value
    return metadata


@dataclass
class Record:
    path: Path
    relative: str
    meta: dict
    text: str

    @property
    def id(self) -> str:
        return self.meta.get("id", "")

    def brief(self) -> dict:
        return {"id": self.id, "type": self.meta.get("type"),
                "title": self.meta.get("title", self.path.stem),
                "status": self.meta.get("status"), "path": self.relative}


def load_records(root: Path) -> tuple[list[Record], list[str]]:
    records, errors = [], []
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not denied((d,)) and not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            if not name.lower().endswith(".md") or denied((name,)):
                continue
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            try:
                safe_path(root, relative)
                if path.stat().st_size > MAX_RECORD_BYTES:
                    raise ForgeError(f"{relative}: Markdown exceeds {MAX_RECORD_BYTES} bytes; split the record before indexing.")
                text = path.read_text(encoding="utf-8")
                meta = parse_header(text, relative)
                if meta is not None:
                    records.append(Record(path, relative, meta, text))
            except (ForgeError, OSError, UnicodeError) as exc:
                errors.append(str(exc))
    return records, errors


def init(project: Path, root: Path, dry_run: bool) -> dict:
    if root.exists() and not root.is_dir():
        raise ForgeError("The selected Forge root is not a directory.")
    config = safe_path(root, "forge.json")
    if config.exists():
        data = read_config(root)
    else:
        data = {"schema_version": 1, "entrypoint": "index.md"}
    entrypoint = safe_path(root, data["entrypoint"])
    planned = []
    if not config.exists():
        planned.append("forge.json")
    if not entrypoint.exists():
        planned.append(data["entrypoint"])
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
        if "forge.json" in planned:
            config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        if data["entrypoint"] in planned:
            entrypoint.parent.mkdir(parents=True, exist_ok=True)
            entrypoint.write_text(
                '---\nid: forge.index\ntype: index\ntitle: Project Forge\nstatus: active\ncoverage: partial\n---\n\n'
                '# Project Forge\n\n'
                'Read this entry point, applicable global constraints, and only the records relevant to the current task. '
                'Existing repository instructions still apply.\n\n'
                '## Routing\n\n'
                'Add short links to existing project documentation, active milestones, topic/component directories, '
                'scoped constraints, and separate acceptance records as they become useful. '
                'Preserve existing documents and source files. Catalog coverage is partial; use a targeted source '
                'search before concluding that a capability does not exist.\n\n'
                '## Current work\n\n'
                'Link the active requirement and milestone here when work is planned. '
                'Keep progress in that milestone and completion criteria in its separate acceptance record.\n',
                encoding="utf-8")
    return {"root": str(root.relative_to(project)), "dry_run": dry_run,
            "created" if not dry_run else "would_create": planned,
            "preserved_existing_files": True,
            "next": "Link existing context, identify applicable user constraints, and seed only the active work."}


def record_map(records: list[Record]) -> tuple[dict[str, Record], list[str]]:
    by_id, errors = {}, []
    for record in records:
        if record.id in by_id:
            errors.append(f"Duplicate ID {record.id!r}: {by_id[record.id].relative}, {record.relative}")
        else:
            by_id[record.id] = record
    return by_id, errors


def local_reference(value: str) -> str | None:
    value = value.strip().strip("<>")
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https", "mailto"} or value.startswith("//"):
        return None
    if parsed.scheme:
        # A line suffix (src/file.py:12) is not a URL scheme.
        if not re.search(r":\d+(?:-\d+)?$", value):
            raise ForgeError(f"Unsupported reference scheme: {value!r}")
    path = unquote(value.split("#", 1)[0].split("?", 1)[0])
    return re.sub(r":\d+(?:-\d+)?$", "", path)


def source_exists(project: Path, value: str) -> bool:
    local = local_reference(value)
    if local is None or not local:
        return True
    safe_path(project, local, allow_glob=True)
    if any(c in local for c in "*?["):
        # glob never reads contents; validate all results before accepting one.
        for result in project.glob(local):
            try:
                safe_path(project, result.relative_to(project).as_posix())
                return True
            except ForgeError:
                continue
        return False
    return (project / local).exists()


def check(project: Path, root: Path, records: list[Record], errors: list[str]) -> dict:
    errors = list(errors)
    by_id, duplicate_errors = record_map(records)
    errors.extend(duplicate_errors)
    warnings = []
    config = read_config(root)
    if not safe_path(root, config["entrypoint"]).is_file():
        errors.append(f"Missing entrypoint: {config['entrypoint']}")
    for record in records:
        meta, label = record.meta, record.relative
        for key in ("id", "type", "title", "status"):
            if not meta.get(key):
                errors.append(f"{label}: missing {key}.")
        if not ID_RE.fullmatch(record.id):
            errors.append(f"{label}: invalid ID {record.id!r}.")
        if meta.get("type") not in TYPES:
            errors.append(f"{label}: unknown type {meta.get('type')!r}.")
        if meta.get("status") not in STATUSES:
            errors.append(f"{label}: unknown status {meta.get('status')!r}.")
        for field in REF_FIELDS:
            for target in meta.get(field, []):
                if target not in by_id:
                    errors.append(f"{label}: {field} references missing ID {target!r}.")
                elif field == "constraints" and by_id[target].meta.get("type") != "constraint":
                    errors.append(f"{label}: {target!r} is not a constraint.")
                elif field == "acceptance" and by_id[target].meta.get("type") != "acceptance":
                    errors.append(f"{label}: {target!r} is not a separate acceptance record.")
        if meta.get("type") == "milestone" and not meta.get("acceptance"):
            errors.append(f"{label}: milestone needs separate acceptance record IDs.")
        if meta.get("type") == "constraint":
            if not meta.get("source"):
                errors.append(f"{label}: constraint needs an instruction source.")
            if not meta.get("scope"):
                errors.append(f"{label}: constraint needs scope (global or project-relative globs).")
        if meta.get("type") == "deviation":
            if not meta.get("constraints"):
                errors.append(f"{label}: deviation must reference its affected constraint IDs.")
            if meta.get("status") in {"approved", "applied", "accepted"} and not meta.get("authorization", "").strip():
                errors.append(f"{label}: accepted deviation requires an explicit authorization reference.")
            if meta.get("status") in {"observed", "open", "proposed"}:
                warnings.append(f"{label}: unresolved deviation; recording it does not authorize departure.")
        for value in meta.get("scope", []):
            if value != "global":
                try:
                    safe_path(project, value, allow_glob=True)
                except ForgeError as exc:
                    errors.append(f"{label}: invalid scope: {exc}")
        for value in meta.get("sources", []):
            try:
                if not source_exists(project, value):
                    errors.append(f"{label}: missing source path {value!r}.")
            except ForgeError as exc:
                errors.append(f"{label}: {exc}")
        for match in LINK_RE.finditer(record.text):
            target = match.group(1)
            try:
                local = local_reference(target)
                if local:
                    # Markdown links are relative to their own document, and may
                    # legitimately reach source code outside the Forge subfolder.
                    base_relative = record.path.parent.relative_to(project)
                    joined = os.path.normpath(str(base_relative / local))
                    path = safe_path(project, joined)
                    if not path.exists():
                        errors.append(f"{label}: missing local link {target!r}.")
            except ForgeError as exc:
                errors.append(f"{label}: invalid local link: {exc}")
        if meta.get("type") in {"topic", "component", "page", "consideration"}:
            verified = meta.get("verified_at")
            if not verified:
                warnings.append(f"{label}: no verified_at date; inspect current sources before relying on it.")
            else:
                try:
                    checked = date.fromisoformat(verified)
                    if (date.today() - checked).days > 90:
                        warnings.append(f"{label}: verification is over 90 days old; this is a freshness hint, not proof of drift.")
                    elif checked > date.today():
                        warnings.append(f"{label}: verified_at is in the future.")
                except ValueError:
                    errors.append(f"{label}: verified_at must use YYYY-MM-DD.")
    return {"root": str(root.relative_to(project)), "records": len(records),
            "errors": errors, "warnings": warnings, "ok": not errors,
            "note": "Checks cover local structure and references, not behavioral correctness or authorization authenticity."}


def find(records: list[Record], query: str, limit: int, include_history: bool) -> dict:
    terms = query.lower().split()
    results = []
    for record in records:
        if not include_history and record.meta.get("status") in HISTORY:
            continue
        haystack = json.dumps(record.meta, ensure_ascii=False).lower() + " " + record.relative.lower()
        if all(term in haystack for term in terms):
            results.append(record.brief())
    return {"matches": results[:limit], "total": len(results), "truncated": len(results) > limit,
            "note": "Metadata search only; absence is not proof that a capability does not exist."}


def scope_matches(pattern: str, path: str) -> bool:
    if pattern == "global":
        return True
    # fnmatch handles broad prefixes; PurePath handles '**' components. A
    # trailing '/**' also includes the directory itself.
    return (fnmatch.fnmatchcase(path, pattern) or PurePosixPath(path).match(pattern)
            or (pattern.endswith("/**") and path == pattern[:-3]))


def impact(project: Path, root: Path, records: list[Record], targets: list[str], limit: int) -> dict:
    by_id, errors = record_map(records)
    if errors:
        raise ForgeError("; ".join(errors))
    reasons: dict[str, set[str]] = {}
    source_paths = set()
    selected_constraints = set()

    def add(record_id: str, reason: str) -> None:
        reasons.setdefault(record_id, set()).add(reason)

    for target in targets:
        if target in by_id:
            add(target, "selected ID")
            if by_id[target].meta.get("type") == "constraint":
                selected_constraints.add(target)
            for source in by_id[target].meta.get("sources", []):
                local = local_reference(source)
                if local:
                    source_paths.add(local)
        else:
            local = local_reference(target)
            if not local:
                raise ForgeError(f"Impact targets must be record IDs or local project paths: {target!r}")
            safe_path(project, local, allow_glob=True)
            source_paths.add(local)
            for record in records:
                if target == record.relative or local == record.path.relative_to(project).as_posix():
                    add(record.id, "selected record path")
                    if record.meta.get("type") == "constraint":
                        selected_constraints.add(record.id)
                for source in record.meta.get("sources", []):
                    source_path = local_reference(source)
                    if source_path and (source_path == local or scope_matches(source_path, local)
                                        or local.startswith(source_path.rstrip("/") + "/")):
                        add(record.id, f"source: {local}")

    # A changed instruction affects explicit consumers and known sources under
    # its scope. This is distinct from merely loading an applicable instruction.
    for constraint_id in selected_constraints:
        scopes = by_id[constraint_id].meta.get("scope", [])
        for record in records:
            if record.id == constraint_id or record.meta.get("status") in HISTORY:
                continue
            if constraint_id in record.meta.get("constraints", []):
                add(record.id, f"uses changed constraint: {constraint_id}")
            elif record.meta.get("type") not in {"index", "constraint", "deviation"}:
                if "global" in scopes:
                    add(record.id, f"changed global constraint: {constraint_id}")
                elif any(scope_matches(scope, local_reference(source) or "")
                         for scope in scopes for source in record.meta.get("sources", [])):
                    add(record.id, f"changed constraint covers source: {constraint_id}")

    # Only depends_on relationships expand transitively. Context associations
    # route useful records, but do not fan out through every shared topic.
    reverse: dict[str, list[str]] = {}
    for record in records:
        for dependency in record.meta.get("depends_on", []):
            reverse.setdefault(dependency, []).append(record.id)
    queue = deque(reasons)
    traversed = set()
    while queue:
        current = queue.popleft()
        if current in traversed:
            continue
        traversed.add(current)
        for dependent in reverse.get(current, []):
            add(dependent, f"depends_on: {current}")
            if dependent not in traversed:
                queue.append(dependent)

    affected = set(reasons)
    # Find directly associated plans/acceptance context once. Newly loaded
    # shared topics do not cause another reverse association fan-out.
    for record in records:
        if record.meta.get("status") in HISTORY:
            continue
        if any(affected.intersection(record.meta.get(field, [])) for field in ("topics", "requirements", "milestones")):
            add(record.id, "direct context association")

    # Follow required context without expanding membership lists. Requirements
    # and acceptance records loaded as context are leaves (their constraints
    # still apply). In particular M03 -> requirement -> milestones must not
    # pull every sibling milestone into a focused change.
    previous_size = -1
    while len(reasons) != previous_size:
        previous_size = len(reasons)
        for record_id in list(reasons):
            record = by_id[record_id]
            if record.meta.get("type") in {"requirement", "acceptance"} and record_id not in affected:
                fields = ("constraints",)
            else:
                fields = ("topics", "depends_on", "constraints", "requirements", "acceptance")
            for field in fields:
                for linked in record.meta.get(field, []):
                    if linked in by_id:
                        add(linked, f"{field}: {record_id}")
            for source in record.meta.get("sources", []):
                local = local_reference(source)
                if local:
                    source_paths.add(local)
        for record in records:
            if record.meta.get("status") in HISTORY:
                continue
            if record.meta.get("type") == "constraint":
                scopes = record.meta.get("scope", [])
                if "global" in scopes:
                    add(record.id, "global constraint")
                elif any(scope_matches(pattern, path) for pattern in scopes for path in source_paths):
                    add(record.id, "constraint scope matches affected source")
        constraint_ids = {key for key in reasons if by_id[key].meta.get("type") == "constraint"}
        for record in records:
            if (record.meta.get("type") == "deviation"
                    and record.meta.get("status") not in HISTORY
                    and constraint_ids.intersection(record.meta.get("constraints", []))):
                add(record.id, "deviation for an applicable constraint")
    ordered = sorted(reasons, key=lambda key: (by_id[key].meta.get("type") != "constraint", by_id[key].relative))
    results = [dict(by_id[key].brief(), reasons=sorted(reasons[key])) for key in ordered]
    return {"targets": targets, "records": results[:limit], "total": len(results),
            "truncated": len(results) > limit,
            "note": "Known impact only. Inspect current source and appropriate checks; missing links do not establish isolation."}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("init", "find", "impact", "check"):
        sub = commands.add_parser(name)
        sub.add_argument("--project", default=".", help="Project directory (default: current directory)")
        sub.add_argument("--root", help="Project-relative context folder; autodetect configured top-level roots")
        if name == "init":
            sub.add_argument("--dry-run", action="store_true")
        elif name == "find":
            sub.add_argument("query", help="Space-separated metadata search terms")
            sub.add_argument("--limit", type=int, default=12)
            sub.add_argument("--include-history", action="store_true")
        elif name == "impact":
            sub.add_argument("targets", nargs="+", help="Record IDs or project-relative source paths")
            sub.add_argument("--limit", type=int, default=30)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if hasattr(args, "limit") and args.limit < 1:
            raise ForgeError("--limit must be positive.")
        project = project_path(args.project)
        root = resolve_root(project, args.root, initialize=args.command == "init")
        if args.command == "init":
            output = init(project, root, args.dry_run)
        else:
            read_config(root)
            records, errors = load_records(root)
            if args.command == "check":
                output = check(project, root, records, errors)
            else:
                if errors:
                    raise ForgeError("; ".join(errors))
                _, duplicate_errors = record_map(records)
                if duplicate_errors:
                    raise ForgeError("; ".join(duplicate_errors))
                if args.command == "find":
                    output = find(records, args.query, args.limit, args.include_history)
                else:
                    output = impact(project, root, records, args.targets, args.limit)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 1 if output.get("errors") else 0
    except (ForgeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
