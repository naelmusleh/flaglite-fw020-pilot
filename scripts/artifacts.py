#!/usr/bin/env python3
"""Dependency-free artifact helper for framework and initialized app repositories."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
APP_CANONICAL_FILES = ("mission.md", "constitution.md", "specification.md", "design.md", "backlog.md")
APP_ARTIFACT_DIRS = ("decisions", "reviews", "architecture", "delivery", "operations", "docs")
APP_STABLE_FILENAMES = {
    "decision-log": "DECISION-LOG.md",
    "architecture-overview": "architecture.md",
    "feasibility-register": "feasibility-register.md",
    "verification-plan": "verification-plan.md",
    "operations-runbook": "RUNBOOK.md",
}
REQUIRED = ("id", "type", "title", "status", "version", "created", "updated")
FRAMEWORK_CONTRACT = Path("docs/framework/ARTIFACT-CONTRACT-001.json")
APP_FRAMEWORK_LOCK = Path(".sdd/framework.lock.json")
CANONICAL_FRAMEWORK_URL = "https://github.com/naelmusleh/adversarial-sdd-boilerplate"
CANONICAL_FRAMEWORK_REPOSITORY = "naelmusleh/adversarial-sdd-boilerplate"
CANONICAL_ATTESTER = CANONICAL_FRAMEWORK_REPOSITORY + "/.github/workflows/sdd-trusted-ci-attest.yml"
APP_HANDOFFS = {
    "G-REQ": Path(".sdd/G-REQ-HANDOFF.json"),
    "G-ARCH": Path(".sdd/G-ARCH-CONTRACT.json"),
}
APP_LOCKED_FILES = (
    "scripts/artifacts.py",
    ".sdd/G-REQ-HANDOFF.json.template",
    ".sdd/G-ARCH-CONTRACT.json.template",
    "docs/templates/app-project/gate-record.md.template",
    ".github/workflows/sdd-contract-validation.yml",
)
APP_LOCKED_FILES_V1 = APP_LOCKED_FILES
APP_GATE_SCHEMA = Path(".sdd/schemas/gate-run-v1.schema.json")
APP_GATE_SCHEMA_V1_1 = Path(".sdd/schemas/gate-run-v1.1.schema.json")
APP_GATE_SCHEMA_V1_2 = Path(".sdd/schemas/gate-run-v1.2.schema.json")
APP_GATE_TEMPLATE = Path(".sdd/gate-run-v1.json.template")
APP_GATE_TEMPLATE_V1_2 = Path(".sdd/gate-run-v1.2.json.template")
APP_GATE_RUNS = Path(".sdd/gate-runs")
APP_LOCKED_FILES_V2 = APP_LOCKED_FILES_V1 + (APP_GATE_SCHEMA.as_posix(), APP_GATE_TEMPLATE.as_posix())
APP_REQUIRED_CHECKS_SCHEMA = Path(".sdd/schemas/required-checks-v1.schema.json")
APP_REQUIRED_CHECKS_TEMPLATE = Path(".sdd/required-checks.json.template")
APP_REQUIRED_CHECKS = Path(".sdd/required-checks.json")
APP_CI_CHECK_RUNNER = "scripts/ci_checks.py"
APP_LOCKED_FILES_V3 = APP_LOCKED_FILES_V2 + (
    APP_REQUIRED_CHECKS_SCHEMA.as_posix(), APP_REQUIRED_CHECKS_TEMPLATE.as_posix(), APP_CI_CHECK_RUNNER,
)
APP_TRUSTED_CI_SCHEMA = Path(".sdd/schemas/trusted-ci-v1.schema.json")
APP_TRUSTED_CI_TEMPLATE = Path(".sdd/trusted-ci.json.template")
APP_TRUSTED_CI = Path(".sdd/trusted-ci.json")
APP_LOCKED_FILES_V4 = APP_LOCKED_FILES_V3 + (
    APP_GATE_SCHEMA_V1_2.as_posix(), APP_GATE_TEMPLATE_V1_2.as_posix(),
    APP_TRUSTED_CI_SCHEMA.as_posix(), APP_TRUSTED_CI_TEMPLATE.as_posix(),
)
APP_LOCK_VERSIONS = {1, 2, 3, 4}
HANDOFF_CONTRACT_VERSION = 1
MAX_JSON_BYTES = 1_048_576
APP_REQUIREMENT_TABLES = (
    {"path": "specification.md", "heading": "## Functional requirements", "requirement_kind": "FR", "minimum_rows": 0},
    {"path": "specification.md", "heading": "## Quality requirements", "requirement_kind": "NFR", "minimum_rows": 0},
)
RFC_2119_KEYWORDS = (
    "MUST NOT", "SHALL NOT", "SHOULD NOT", "MUST", "REQUIRED", "SHALL",
    "SHOULD", "RECOMMENDED", "MAY", "OPTIONAL",
)
ALLOWED_STATUSES = {
    "draft", "in-review", "revision-required", "approved", "active",
    "blocked", "superseded", "retired",
}
ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3}$")
KEY_RE = re.compile(r"^([a-z][a-z0-9-]*):\s*(.*?)\s*$")
FRAMEWORK_REVISION_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
RELEASE_WINDOW_RE = re.compile(r"^release-window: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))/(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))$")
GATE_RESULTS = {"not-run", "passed", "failed", "blocked", "passed-with-accepted-risk", "not-applicable"}
GATE_IDS = {
    "G-INTENT", "G-SETUP", "G-REQ", "G-FEAS", "G-COVERAGE",
    "G-CX", "G-ARCH", "G-IMPL", "G-RELEASE", "G-OPERATE",
}
GATE_ORDER = (
    "G-INTENT", "G-SETUP", "G-REQ", "G-FEAS", "G-COVERAGE",
    "G-CX", "G-ARCH", "G-IMPL", "G-RELEASE", "G-OPERATE",
)
GATE_CRITERIA = {
    "G-INTENT": ("GINT-01", "GINT-02", "GINT-03"),
    "G-SETUP": ("GSET-01", "GSET-02", "GSET-03"),
    "G-REQ": ("GREQ-01", "GREQ-02", "GREQ-03", "GREQ-04"),
    "G-FEAS": ("GFEAS-01", "GFEAS-02", "GFEAS-03"),
    "G-COVERAGE": ("GCOV-01", "GCOV-02", "GCOV-03"),
    "G-CX": ("GCX-01", "GCX-02", "GCX-03"),
    "G-ARCH": ("GARCH-01", "GARCH-02", "GARCH-03"),
    "G-IMPL": ("GIMPL-01", "GIMPL-02", "GIMPL-03"),
    "G-RELEASE": ("GREL-01", "GREL-02", "GREL-03"),
    "G-OPERATE": ("GOP-01", "GOP-02", "GOP-03"),
}
GATE_RESULT_TRANSITIONS = {
    None: {"not-ready", "in-progress", "blocked", "not-applicable"},
    "not-ready": {"in-progress", "blocked", "not-applicable"},
    "in-progress": {"passed", "failed", "blocked", "passed-with-accepted-risk", "not-applicable"},
    "failed": {"in-progress", "blocked", "not-applicable"},
    "blocked": {"in-progress", "not-applicable"},
    "passed": set(GATE_RESULTS),
    "passed-with-accepted-risk": set(GATE_RESULTS),
    "not-applicable": set(GATE_RESULTS),
}
JSON_SCHEMA_SUPPORTED_KEYWORDS = {
    "$schema", "$id", "$defs", "title", "description", "$ref", "type",
    "required", "properties", "additionalProperties", "const", "enum",
    "pattern", "minLength", "maxLength", "minimum", "minItems", "maxItems",
    "uniqueItems", "items", "contains", "minContains", "maxContains",
    "allOf", "oneOf", "if", "then", "else", "format", "minProperties",
}


def is_app_project(root: Path) -> bool:
    """Recognize an app SDD repository, including an incomplete one.

    Any canonical root document is enough to identify the app layout. Requiring
    every file here made a damaged app repository fall back to framework mode,
    where validation could misleadingly succeed with zero artifacts.
    """
    return any((root / filename).is_file() for filename in APP_CANONICAL_FILES)


def missing_app_canonical_files(root: Path) -> tuple[str, ...]:
    """Return required app SDD documents that are absent from a recognized app."""
    if not is_app_project(root):
        return ()
    return tuple(filename for filename in APP_CANONICAL_FILES if not (root / filename).is_file())


def artifact_roots(root: Path) -> tuple[Path, ...]:
    if is_app_project(root):
        return tuple([root / filename for filename in APP_CANONICAL_FILES] + [root / name for name in APP_ARTIFACT_DIRS])
    return (root / "docs", root / "framework", root / "workflows")


def markdown_files(root: Path = ROOT) -> list[Path]:
    files: set[Path] = set()
    for base in artifact_roots(root):
        if base.is_file() and base.suffix.lower() == ".md":
            files.add(base)
            continue
        if not base.is_dir():
            continue
        files.update(p for p in base.rglob("*.md") if p.is_file())
    # Templates are scaffolding, never live framework or app artifacts.
    files = {p for p in files if not (root / "docs" / "templates" in p.parents)}
    return sorted(files)


def read_front_matter(path: Path) -> tuple[dict[str, str], str | None]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return {}, str(exc)
    if not lines or lines[0].strip() != "---":
        return {}, "missing front matter opening delimiter"
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, "missing front matter closing delimiter"
    data: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], 2):
        if not line.strip():
            continue
        match = KEY_RE.match(line)
        if not match:
            return data, f"unsupported front matter at line {number}; expected flat key: value"
        key, value = match.groups()
        if key in data:
            return data, f"duplicate metadata key: {key}"
        data[key] = value.strip().strip("\"'")
    return data, None


def load_json_object(path: Path) -> tuple[dict[str, object] | None, str | None]:
    """Load strict JSON, rejecting duplicate keys instead of silently keeping the last value."""
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key '{key}'")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-standard JSON constant '{value}'")

    try:
        if path.stat().st_size > MAX_JSON_BYTES:
            return None, f"JSON file exceeds {MAX_JSON_BYTES} byte limit"
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "top-level JSON value must be an object"
    return value, None


def file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha256(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def parse_release_window(value: object) -> tuple[dt.datetime, dt.datetime] | None:
    """Parse an explicit, bounded UTC/offset release window."""
    if not isinstance(value, str):
        return None
    match = RELEASE_WINDOW_RE.fullmatch(value)
    if not match:
        return None
    try:
        start = dt.datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(match.group(2).replace("Z", "+00:00"))
    except ValueError:
        return None
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        return None
    return start, end


def check_frozen_artifact(root: Path, item: object, label: str) -> list[str]:
    if not isinstance(item, dict) or set(item) != {"path", "id", "version", "sha256"}:
        return [f"{label}: each frozen artifact must define exactly path, id, version, and sha256"]
    relative, expected_id, expected_version, expected_digest = (
        item.get("path"), item.get("id"), item.get("version"), item.get("sha256")
    )
    if not all(isinstance(value, str) and value.strip() for value in (relative, expected_id, expected_version)):
        return [f"{label}: frozen artifact path, id, and version must be non-empty strings"]
    if not isinstance(expected_digest, str) or not SHA256_RE.fullmatch(expected_digest):
        return [f"{label} ({relative}): sha256 must use the form sha256:<64 lowercase hexadecimal characters>"]
    path, error = safe_file(root, relative)
    if error or path is None:
        return [f"{label} ({relative}): {error or 'could not resolve file'}"]
    metadata, metadata_error = read_front_matter(path)
    if metadata_error:
        return [f"{label} ({relative}): frozen artifact metadata could not be read: {metadata_error}"]
    problems = []
    if metadata.get("id") != expected_id:
        problems.append(f"{label} ({relative}): expected artifact ID '{expected_id}', found '{metadata.get('id', '')}'")
    if metadata.get("version") != expected_version:
        problems.append(f"{label} ({relative}): expected version '{expected_version}', found '{metadata.get('version', '')}'")
    if file_sha256(path) != expected_digest:
        problems.append(f"{label} ({relative}): frozen file digest does not match")
    return problems


def check_review_reference(root: Path, value: object, label: str) -> list[str]:
    expected_fields = {"path", "id", "version", "sha256", "reviewer_mode", "result"}
    if not isinstance(value, dict) or set(value) != expected_fields:
        return [f"{label}: independent_review must define exactly {', '.join(sorted(expected_fields))}"]
    if value.get("reviewer_mode") != "independent" or value.get("result") != "PASS":
        return [f"{label}: handoff requires an independent review with result PASS"]
    return check_frozen_artifact(
        root,
        {key: value.get(key) for key in ("path", "id", "version", "sha256")},
        label + " independent_review",
    )


def validate_handoff_manifest(root: Path, gate_id: str, revision: str) -> list[str]:
    manifest_path = APP_HANDOFFS[gate_id]
    path, error = safe_file(root, manifest_path.as_posix())
    if error or path is None:
        return [f"{manifest_path.as_posix()}: required handoff manifest {error or 'is missing'}"]
    manifest, parse_error = load_json_object(path)
    if parse_error or manifest is None:
        return [f"{manifest_path.as_posix()}: invalid JSON handoff manifest: {parse_error or 'invalid object'}"]

    if gate_id == "G-REQ":
        expected_fields = {"contract_id", "contract_version", "framework_revision", "source_gate", "scope", "frozen_artifacts", "independent_review"}
        expected_id = "G-REQ-HANDOFF-001"
        required_paths = {"mission.md", "constitution.md", "specification.md", "backlog.md"}
    else:
        expected_fields = {"contract_id", "contract_version", "framework_revision", "source_gate", "scope", "frozen_artifacts", "contract_file", "required_checks", "review_inputs", "independent_review"}
        expected_id = "G-ARCH-CONTRACT-001"
        required_paths = {"specification.md", "design.md", "backlog.md"}

    problems: list[str] = []
    if set(manifest) != expected_fields:
        problems.append(f"{manifest_path.as_posix()}: fields must be exactly {', '.join(sorted(expected_fields))}")
    if manifest.get("contract_id") != expected_id or manifest.get("contract_version") != HANDOFF_CONTRACT_VERSION:
        problems.append(f"{manifest_path.as_posix()}: unsupported contract identity or version")
    if manifest.get("source_gate") != gate_id:
        problems.append(f"{manifest_path.as_posix()}: source_gate must be '{gate_id}'")
    if manifest.get("framework_revision") != revision:
        problems.append(f"{manifest_path.as_posix()}: framework_revision does not match .sdd/framework.lock.json")
    scope = manifest.get("scope")
    if not isinstance(scope, str) or not scope.strip() or "<" in scope or ">" in scope:
        problems.append(f"{manifest_path.as_posix()}: scope must be a populated string without template markers")

    frozen_artifacts = manifest.get("frozen_artifacts")
    if not isinstance(frozen_artifacts, list) or not frozen_artifacts:
        problems.append(f"{manifest_path.as_posix()}: frozen_artifacts must be a non-empty array")
    else:
        seen_paths: set[str] = set()
        observed_paths: set[str] = set()
        for index, item in enumerate(frozen_artifacts, 1):
            label = f"{manifest_path.as_posix()} frozen_artifacts[{index}]"
            problems.extend(check_frozen_artifact(root, item, label))
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                relative = item["path"]
                if relative in seen_paths:
                    problems.append(f"{label}: duplicate frozen artifact path '{relative}'")
                seen_paths.add(relative)
                observed_paths.add(relative)
        for required_path in sorted(required_paths - observed_paths):
            problems.append(f"{manifest_path.as_posix()}: frozen_artifacts must include '{required_path}'")

    problems.extend(check_review_reference(root, manifest.get("independent_review"), manifest_path.as_posix()))

    if gate_id == "G-ARCH":
        contract_file = manifest.get("contract_file")
        if not isinstance(contract_file, dict) or set(contract_file) != {"path", "sha256"}:
            problems.append(f"{manifest_path.as_posix()}: contract_file must define exactly path and sha256")
        else:
            contract_path, contract_error = safe_file(root, str(contract_file.get("path", "")))
            digest = contract_file.get("sha256")
            if contract_error or contract_path is None:
                problems.append(f"{manifest_path.as_posix()} contract_file: {contract_error or 'file is missing'}")
            elif not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                problems.append(f"{manifest_path.as_posix()} contract_file: sha256 is malformed")
            elif file_sha256(contract_path) != digest:
                problems.append(f"{manifest_path.as_posix()} contract_file: frozen contract digest does not match")
        checks = manifest.get("required_checks")
        if not isinstance(checks, list) or not checks:
            problems.append(f"{manifest_path.as_posix()}: required_checks must be a non-empty array")
        else:
            check_ids: set[str] = set()
            for index, check in enumerate(checks, 1):
                label = f"{manifest_path.as_posix()} required_checks[{index}]"
                if not isinstance(check, dict) or set(check) != {"id", "command", "assertions"}:
                    problems.append(f"{label}: each check must define exactly id, command, and assertions")
                    continue
                check_id, command, assertions = check.get("id"), check.get("command"), check.get("assertions")
                if not isinstance(check_id, str) or not check_id.strip() or check_id in check_ids:
                    problems.append(f"{label}: id must be a unique non-empty string")
                else:
                    check_ids.add(check_id)
                if not isinstance(command, str) or not command.strip() or "<" in command or ">" in command:
                    problems.append(f"{label}: command must be a populated exact command")
                if not isinstance(assertions, list) or not assertions or not all(isinstance(item, str) and item.strip() for item in assertions):
                    problems.append(f"{label}: assertions must be a non-empty array of non-empty strings")
        review_inputs = manifest.get("review_inputs")
        if not isinstance(review_inputs, list):
            problems.append(f"{manifest_path.as_posix()}: review_inputs must be an array")
        else:
            purposes: set[str] = set()
            for index, review_input in enumerate(review_inputs, 1):
                label = f"{manifest_path.as_posix()} review_inputs[{index}]"
                if not isinstance(review_input, dict) or set(review_input) != {"purpose", "path", "id", "version", "sha256"}:
                    problems.append(f"{label}: each review input must define exactly purpose, path, id, version, and sha256")
                    continue
                purpose = review_input.get("purpose")
                if not isinstance(purpose, str) or not purpose.strip():
                    problems.append(f"{label}: purpose must be a non-empty string")
                    continue
                if purpose not in {"historical-rule-index", "domain-contract", "security-review", "other"}:
                    problems.append(f"{label}: unsupported review input purpose '{purpose}'")
                problems.extend(
                    check_frozen_artifact(
                        root,
                        {key: review_input.get(key) for key in ("path", "id", "version", "sha256")},
                        label,
                    )
                )
                if isinstance(purpose, str):
                    key = f"{purpose}:{review_input.get('path')}"
                    if key in purposes:
                        problems.append(f"{label}: duplicate review input '{key}'")
                    purposes.add(key)
    return problems


def _schema_children(schema: object) -> list[object]:
    if not isinstance(schema, dict):
        return []
    children: list[object] = []
    for keyword in ("$defs", "properties"):
        value = schema.get(keyword)
        if isinstance(value, dict):
            children.extend(value.values())
    for keyword in ("items", "contains", "additionalProperties", "if", "then", "else"):
        value = schema.get(keyword)
        if isinstance(value, (dict, bool)):
            children.append(value)
    for keyword in ("allOf", "oneOf"):
        value = schema.get(keyword)
        if isinstance(value, list):
            children.extend(value)
    return children


def schema_definition_problems(schema: object, pointer: str = "#") -> list[str]:
    """Reject schema keywords this dependency-free Draft 2020-12 subset cannot enforce."""
    if isinstance(schema, bool):
        return []
    if not isinstance(schema, dict):
        return [f"{pointer}: schema node must be an object or boolean"]
    problems = [f"{pointer}: unsupported JSON Schema keyword '{key}'" for key in schema if key not in JSON_SCHEMA_SUPPORTED_KEYWORDS]
    string_keywords = {"$schema", "$id", "title", "description", "pattern", "format"}
    for key in string_keywords & schema.keys():
        if not isinstance(schema[key], str):
            problems.append(f"{pointer}/{key}: must be a string")
    if "type" in schema:
        value = schema["type"]
        allowed_types = {"object", "array", "string", "boolean", "null", "integer", "number"}
        if not (isinstance(value, str) and value in allowed_types) and not (
            isinstance(value, list) and value and all(isinstance(item, str) and item in allowed_types for item in value)
        ):
            problems.append(f"{pointer}/type: must be a supported JSON type or non-empty array of types")
    if "$ref" in schema and (not isinstance(schema["$ref"], str) or not schema["$ref"].startswith("#/")):
        problems.append(f"{pointer}/$ref: only local JSON Pointer references are supported")
    if "format" in schema:
        if not isinstance(schema["format"], str):
            problems.append(f"{pointer}/format: must be a string")
        elif schema["format"] not in {"date", "date-time"}:
            problems.append(f"{pointer}/format: unsupported format; supported formats are date and date-time")
    if "required" in schema and (not isinstance(schema["required"], list) or not all(isinstance(item, str) for item in schema["required"])):
        problems.append(f"{pointer}/required: must be an array of strings")
    for key in ("properties", "$defs"):
        if key in schema and (not isinstance(schema[key], dict) or not all(isinstance(name, str) for name in schema[key])):
            problems.append(f"{pointer}/{key}: must be an object keyed by strings")
    for key in ("items", "contains", "additionalProperties", "if", "then", "else"):
        if key in schema and not isinstance(schema[key], (dict, bool)):
            problems.append(f"{pointer}/{key}: must be a schema object or boolean")
    for key in ("allOf", "oneOf"):
        if key in schema and (not isinstance(schema[key], list) or not schema[key]):
            problems.append(f"{pointer}/{key}: must be a non-empty array of schemas")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        problems.append(f"{pointer}/enum: must be a non-empty array")
    for key in ("minLength", "maxLength", "minItems", "maxItems", "minContains", "maxContains", "minProperties"):
        if key in schema and (not isinstance(schema[key], int) or isinstance(schema[key], bool) or schema[key] < 0):
            problems.append(f"{pointer}/{key}: must be a non-negative integer")
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        problems.append(f"{pointer}/uniqueItems: must be a boolean")
    if "minimum" in schema and (not isinstance(schema["minimum"], (int, float)) or isinstance(schema["minimum"], bool)):
        problems.append(f"{pointer}/minimum: must be a number")
    if "pattern" in schema and isinstance(schema["pattern"], str):
        try:
            re.compile(schema["pattern"])
        except re.error:
            problems.append(f"{pointer}/pattern: invalid regular expression")
    for child in _schema_children(schema):
        problems.extend(schema_definition_problems(child, pointer))
    if schema.get("$schema") not in (None, "https://json-schema.org/draft/2020-12/schema"):
        problems.append(f"{pointer}: only JSON Schema Draft 2020-12 is supported")
    return problems


def _json_type_matches(value: object, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "null": value is None,
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }.get(expected, False)


def _resolve_schema_ref(root_schema: dict[str, object], ref: str) -> object | None:
    if not ref.startswith("#/"):
        return None
    current: object = root_schema
    for segment in ref[2:].split("/"):
        segment = segment.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def validate_schema_value(
    value: object,
    schema: object,
    root_schema: dict[str, object],
    instance_path: str = "$",
    depth: int = 0,
) -> list[str]:
    """Validate the contract schema subset using only the Python standard library.

    Unsupported schema keywords are rejected before this evaluator is called, so
    a schema edit cannot silently weaken validation by adding an ignored rule.
    """
    if depth > 100:
        return [f"{instance_path}: schema evaluation exceeded the nesting limit"]
    if schema is True:
        return []
    if schema is False or not isinstance(schema, dict):
        return [f"{instance_path}: schema definition is invalid or forbids this value"]
    problems: list[str] = []
    next_depth = depth + 1

    ref = schema.get("$ref")
    if ref is not None:
        target = _resolve_schema_ref(root_schema, ref) if isinstance(ref, str) else None
        if target is None:
            return [f"{instance_path}: unresolved or unsupported schema reference {ref!r}"]
        problems.extend(validate_schema_value(value, target, root_schema, instance_path, next_depth))

    expected_type = schema.get("type")
    if expected_type is not None:
        alternatives = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_json_type_matches(value, kind) for kind in alternatives if isinstance(kind, str)):
            return [f"{instance_path}: expected JSON type {' or '.join(str(x) for x in alternatives)}"]
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        problems.append(f"{instance_path}: value does not equal required constant {schema['const']!r}")
    if "enum" in schema:
        if not any(type(value) is type(option) and value == option for option in schema["enum"]):
            problems.append(f"{instance_path}: value is not one of the allowed values")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                problems.append(f"{instance_path}: missing required property '{key}'")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in value:
                    problems.extend(validate_schema_value(value[key], child_schema, root_schema, f"{instance_path}.{key}", next_depth))
        additional = schema.get("additionalProperties", True)
        for key in value:
            if not isinstance(properties, dict) or key not in properties:
                if additional is False:
                    problems.append(f"{instance_path}.{key}: additional property is not allowed")
                elif isinstance(additional, (dict, bool)):
                    problems.extend(validate_schema_value(value[key], additional, root_schema, f"{instance_path}.{key}", next_depth))
        if len(value) < schema.get("minProperties", 0):
            problems.append(f"{instance_path}: object has fewer than {schema['minProperties']} properties")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            problems.append(f"{instance_path}: array has fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            problems.append(f"{instance_path}: array has more than {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for item in value]
            if len(set(serialized)) != len(serialized):
                problems.append(f"{instance_path}: array items must be unique")
        if "items" in schema:
            for index, item in enumerate(value):
                problems.extend(validate_schema_value(item, schema["items"], root_schema, f"{instance_path}[{index}]", next_depth))
        if "contains" in schema:
            matches = sum(not validate_schema_value(item, schema["contains"], root_schema, f"{instance_path}[{index}]", next_depth) for index, item in enumerate(value))
            minimum = schema.get("minContains", 1)
            maximum = schema.get("maxContains")
            if matches < minimum or (maximum is not None and matches > maximum):
                problems.append(f"{instance_path}: contains matched {matches} items; expected {minimum}..{maximum or 'unbounded'}")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            problems.append(f"{instance_path}: string is shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            problems.append(f"{instance_path}: string is longer than {schema['maxLength']} characters")
        if "pattern" in schema:
            try:
                if re.search(schema["pattern"], value) is None:
                    problems.append(f"{instance_path}: string does not match required pattern")
            except re.error:
                problems.append(f"{instance_path}: schema contains an invalid regular expression")
        fmt = schema.get("format")
        if fmt in {"date", "date-time"}:
            try:
                if fmt == "date":
                    dt.date.fromisoformat(value)
                else:
                    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError("timezone is required")
            except ValueError:
                problems.append(f"{instance_path}: value is not a valid {fmt}")

    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        problems.append(f"{instance_path}: number is below minimum {schema['minimum']}")

    for child in schema.get("allOf", []):
        problems.extend(validate_schema_value(value, child, root_schema, instance_path, next_depth))
    if "oneOf" in schema:
        valid_branches = sum(not validate_schema_value(value, branch, root_schema, instance_path, next_depth) for branch in schema["oneOf"])
        if valid_branches != 1:
            problems.append(f"{instance_path}: value must match exactly one schema alternative; matched {valid_branches}")
    if "if" in schema:
        if_valid = not validate_schema_value(value, schema["if"], root_schema, instance_path, next_depth)
        branch = schema.get("then") if if_valid else schema.get("else")
        if branch is not None:
            problems.extend(validate_schema_value(value, branch, root_schema, instance_path, next_depth))
    return problems


def _app_contract_id_and_version(lock: dict[str, object], lock_version: int) -> tuple[str | None, str | None]:
    if lock_version == 1:
        return None, None
    contract_id = lock.get("gate_contract_id")
    contract_version = lock.get("gate_contract_version")
    return (contract_id, contract_version) if isinstance(contract_id, str) and isinstance(contract_version, str) else (None, None)


def _gate_schema_for_app(root: Path, contract_version: str) -> tuple[dict[str, object] | None, list[str]]:
    schema_path_by_version = {"1.0": APP_GATE_SCHEMA, "1.1": APP_GATE_SCHEMA_V1_1, "1.2": APP_GATE_SCHEMA_V1_2}
    schema_relative = schema_path_by_version.get(contract_version)
    if schema_relative is None:
        return None, [f"{APP_FRAMEWORK_LOCK.as_posix()}: unsupported gate contract version '{contract_version}'"]
    schema_path, path_error = safe_file(root, schema_relative.as_posix())
    if path_error or schema_path is None:
        return None, [f"{schema_relative.as_posix()}: {path_error or 'schema file is unavailable'}"]
    schema, parse_error = load_json_object(schema_path)
    if parse_error or schema is None:
        return None, [f"{schema_relative.as_posix()}: invalid JSON Schema: {parse_error or 'invalid object'}"]
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        return None, [f"{schema_relative.as_posix()}: unsupported JSON Schema dialect"]
    problems = schema_definition_problems(schema)
    if problems:
        return None, [f"{schema_relative.as_posix()}: {problem}" for problem in problems]
    if schema.get("properties", {}).get("contract_version", {}).get("const") != contract_version:
        return None, [f"{schema_relative.as_posix()}: schema contract version does not match the framework lock"]
    return schema, []


def _check_gate_artifact_ref(root: Path, ref: object, label: str, gate_records: dict[str, tuple[Path, dict[str, object]]] | None = None) -> list[str]:
    if not isinstance(ref, dict):
        return [f"{label}: artifact reference must be an object"]
    relative = ref.get("path")
    if not isinstance(relative, str):
        return [f"{label}: path must be a repository-relative string"]
    path, error = safe_file(root, relative)
    if error or path is None:
        return [f"{label} ({relative}): {error or 'could not resolve file'}"]
    problems: list[str] = []
    actual_digest = file_sha256(path)
    if ref.get("sha256") != actual_digest:
        problems.append(f"{label} ({relative}): artifact digest is stale")
    if relative.startswith(APP_GATE_RUNS.as_posix() + "/"):
        if gate_records is None:
            return problems + [f"{label} ({relative}): gate-run reference cannot be resolved"]
        match = next((entry for entry in gate_records.values() if entry[0] == path), None)
        if match is None:
            return problems + [f"{label} ({relative}): referenced gate-run record is not a validated record"]
        gate_record = match[1]
        if ref.get("artifact_id") != gate_record.get("record_id") or str(ref.get("version")) != str(gate_record.get("record_version")):
            problems.append(f"{label} ({relative}): referenced gate-run identity/version does not match")
        return problems
    metadata, metadata_error = read_front_matter(path)
    if metadata_error:
        return problems + [f"{label} ({relative}): referenced artifact has invalid front matter: {metadata_error}"]
    if ref.get("artifact_id") != metadata.get("id"):
        problems.append(f"{label} ({relative}): artifact ID does not match referenced file")
    if ref.get("version") != metadata.get("version"):
        problems.append(f"{label} ({relative}): artifact version does not match referenced file")
    source_revision = ref.get("source_revision")
    if source_revision is not None and (not isinstance(source_revision, str) or not FRAMEWORK_REVISION_RE.fullmatch(source_revision)):
        problems.append(f"{label} ({relative}): source_revision must be null for digest-pinned archive evidence or a 40-character lowercase commit SHA")
    return problems


def _id_occurs_in_paths(root: Path, artifact_id: object, relatives: tuple[str, ...]) -> bool:
    if not isinstance(artifact_id, str) or not artifact_id:
        return False
    pattern = re.compile(rf"(?<![A-Z0-9-]){re.escape(artifact_id)}(?![A-Z0-9-])")
    for relative in relatives:
        path = root / relative
        candidates = [path] if path.is_file() else sorted(path.rglob("*.md")) if path.is_dir() else []
        for candidate in candidates:
            try:
                relative = candidate.relative_to(root).as_posix()
                safe_path, error = safe_file(root, relative)
                if not error and safe_path is not None and pattern.search(safe_path.read_text(encoding="utf-8")):
                    return True
            except (OSError, UnicodeError):
                continue
    return False


def _latest_gate_runs(records: dict[str, tuple[Path, dict[str, object]]]) -> tuple[dict[str, tuple[Path, dict[str, object]]], list[str]]:
    superseded: dict[str, list[str]] = {}
    problems: list[str] = []
    for record_id, (_, record) in records.items():
        previous = record.get("supersedes_run_id")
        if previous is not None:
            if previous not in records:
                problems.append(f"{record_id}: supersedes_run_id '{previous}' does not resolve to a gate-run record")
                continue
            prior_path, prior = records[previous]
            if prior.get("gate_id") != record.get("gate_id"):
                problems.append(f"{record_id}: superseded run belongs to a different gate")
            if record.get("record_version") != prior.get("record_version", 0) + 1:
                problems.append(f"{record_id}: record_version must increment the superseded run version by exactly one")
            allowed = GATE_RESULT_TRANSITIONS.get(prior.get("gate_result"), set())
            if record.get("gate_result") not in allowed:
                problems.append(f"{record_id}: illegal gate-result transition from {prior.get('gate_result')} to {record.get('gate_result')}")
            try:
                current_time = dt.datetime.fromisoformat(str(record.get("created_at", "")).replace("Z", "+00:00"))
                prior_time = dt.datetime.fromisoformat(str(prior.get("created_at", "")).replace("Z", "+00:00"))
                if current_time.tzinfo is None or prior_time.tzinfo is None or current_time <= prior_time:
                    problems.append(f"{record_id}: rerun created_at must be timezone-aware and later than superseded run")
            except ValueError:
                problems.append(f"{record_id}: rerun created_at and superseded run timestamp must be valid ISO date-times")
            superseded.setdefault(previous, []).append(record_id)
    for previous, replacements in superseded.items():
        if len(replacements) > 1:
            problems.append(f"{previous}: immutable gate-run record is superseded by more than one run")
    roots_by_gate: dict[str, list[str]] = {}
    for record_id, (_, record) in records.items():
        if record.get("supersedes_run_id") is None:
            roots_by_gate.setdefault(str(record.get("gate_id")), []).append(record_id)
    for gate_id, root_ids in roots_by_gate.items():
        if len(root_ids) > 1:
            problems.append(f"{gate_id}: multiple unlinked gate-run histories exist; explicitly link the superseding run")
    latest: dict[str, tuple[Path, dict[str, object]]] = {}
    for record_id, entry in records.items():
        if record_id not in superseded:
            gate_id = str(entry[1].get("gate_id"))
            if gate_id in latest:
                problems.append(f"{gate_id}: multiple unsuperseded gate-run records exist")
            latest[gate_id] = entry
    for record_id, (_, record) in records.items():
        gate_id = record.get("gate_id")
        if record.get("supersedes_run_id") is None and record.get("gate_result") not in GATE_RESULT_TRANSITIONS[None]:
            problems.append(f"{record_id}: first gate run cannot have result '{record.get('gate_result')}'")
        if gate_id not in GATE_ORDER:
            continue
        index = GATE_ORDER.index(gate_id)
        # Historical PASS records remain immutable evidence, but only the current
        # unsuperseded run can authorize downstream work against current upstream state.
        if record.get("gate_result") in {"passed", "passed-with-accepted-risk"} and record_id not in superseded:
            scope = record.get("scope", {})
            refs = scope.get("artifact_refs", []) if isinstance(scope, dict) else []
            refs_by_path = {ref.get("path"): ref for ref in refs if isinstance(ref, dict)}
            for upstream_gate in GATE_ORDER[:index]:
                upstream = latest.get(upstream_gate)
                if upstream is None:
                    problems.append(f"{record_id}: cannot pass {gate_id}; required upstream gate {upstream_gate} has no current run")
                    continue
                upstream_path, upstream_record = upstream
                if upstream_record.get("gate_result") not in {"passed", "passed-with-accepted-risk", "not-applicable"}:
                    problems.append(f"{record_id}: cannot pass {gate_id}; latest {upstream_gate} result is {upstream_record.get('gate_result')}")
                try:
                    downstream_time = dt.datetime.fromisoformat(str(record.get("created_at", "")).replace("Z", "+00:00"))
                    upstream_time = dt.datetime.fromisoformat(str(upstream_record.get("created_at", "")).replace("Z", "+00:00"))
                    if downstream_time.tzinfo is None or upstream_time.tzinfo is None or downstream_time <= upstream_time:
                        problems.append(f"{record_id}: passing {gate_id} run must be timezone-aware and later than upstream {upstream_gate} run")
                except ValueError:
                    problems.append(f"{record_id}: passing {gate_id} and upstream {upstream_gate} timestamps must be valid ISO date-times")
                # Require a content-addressed scope reference to the exact current upstream run.
                try:
                    relative_path = upstream_path.relative_to(records[record_id][0].parents[2]).as_posix()
                except ValueError:
                    relative_path = upstream_path.as_posix()
                ref = refs_by_path.get(relative_path)
                if ref is None:
                    problems.append(f"{record_id}: scope.artifact_refs must pin current upstream run {upstream_record.get('record_id')} at {relative_path}")
                elif ref.get("artifact_id") != upstream_record.get("record_id") or str(ref.get("version")) != str(upstream_record.get("record_version")) or ref.get("sha256") != file_sha256(upstream_path):
                    problems.append(f"{record_id}: upstream gate reference for {upstream_gate} is stale or identifies another run")
    return latest, problems


def _published_checkpoint_problems(
    change_control: object,
    source_commit: object,
    authority: object,
    required_task_ids: object,
    label: str,
) -> list[str]:
    if not isinstance(change_control, dict):
        return [f"{label}: a published change_control record is required"]
    problems: list[str] = []
    if not isinstance(source_commit, str) or not FRAMEWORK_REVISION_RE.fullmatch(source_commit):
        problems.append(f"{label}: a passing implementation/release requires an exact source commit SHA")
    if change_control.get("commit_sha") != source_commit:
        problems.append(f"{label}: change_control.commit_sha must match the exact source snapshot")
    if change_control.get("push_result") != "pushed":
        problems.append(f"{label}: push_result must be 'pushed'; a missing or unavailable remote is a blocker")
    for field in ("branch_ref", "remote", "authorization_ref"):
        value = change_control.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{label}: published checkpoint requires non-empty change_control.{field}")
    authorization_ref = change_control.get("authorization_ref")
    authority_obj = authority if isinstance(authority, dict) else {}
    owner = authority_obj.get("accountable_owner", {})
    owner_identity = owner.get("identity") if isinstance(owner, dict) else None
    decisions = authority_obj.get("owner_decisions", [])
    decision = next((item for item in decisions if isinstance(item, dict) and item.get("decision_id") == authorization_ref), None) if isinstance(decisions, list) else None
    if decision is None:
        problems.append(f"{label}: change_control.authorization_ref must resolve to an owner decision in this gate record")
    else:
        choice = str(decision.get("choice", "")).lower()
        if decision.get("decision_maker") != owner_identity:
            problems.append(f"{label}: publication authorization must be made by the accountable owner")
        if "authoriz" not in choice or not any(action in choice for action in ("publish", "push", "commit", "release")):
            problems.append(f"{label}: owner decision must explicitly authorize commit, push, publication, or release")
        if "G-IMPL" in label:
            parts = [part.strip() for part in choice.split(";")]
            fields = {}
            for part in parts[1:]:
                key, separator, value = part.partition("=")
                if separator:
                    fields[key.strip()] = value.strip()
            if parts[0] not in {"authorize-commit", "authorize-push", "authorize-publish"} or any(
                fields.get(key) != str(value).lower()
                for key, value in (("commit_sha", source_commit), ("branch_ref", change_control.get("branch_ref")), ("remote", change_control.get("remote")))
            ):
                problems.append(f"{label}: owner authorization must use authorize-commit/push/publish with exact commit_sha, branch_ref, and remote fields")
        affected = decision.get("affected_ids", [])
        tasks = required_task_ids if isinstance(required_task_ids, list) else []
        if not isinstance(affected, list) or not tasks or not set(tasks).intersection(affected):
            problems.append(f"{label}: publication authorization must identify at least one in-scope task")
    return problems


def _has_independent_reviewer(reviewers: object) -> bool:
    """Require an explicit no-author-overlap declaration for independent reviews."""
    if not isinstance(reviewers, list):
        return False
    return any(
        isinstance(item, dict)
        and item.get("mode") == "independent"
        and item.get("result") == "pass"
        and isinstance(item.get("context_disclosure"), str)
        and bool(item["context_disclosure"].strip())
        and isinstance(item.get("author_overlap"), str)
        and item["author_overlap"].strip().casefold() == "none"
        for item in reviewers
    )


def _ci_change_control_reference_problems(change_control: object, evidence: object, label: str) -> list[str]:
    if not isinstance(change_control, dict) or not isinstance(evidence, dict):
        return [f"{label}: CI evidence and change_control record are required"]
    details = evidence.get("details")
    if not isinstance(details, dict):
        return [f"{label}: CI evidence details are required"]
    if details.get("provider") == "github-actions":
        run_ref = details.get("run_id_or_url")
        if not isinstance(run_ref, str) or not re.search(r"/actions/runs/\d+/attempts/\d+(?:[/?#].*)?$", run_ref):
            return [f"{label}: GitHub Actions evidence must link the exact run attempt URL, including /attempts/<attempt>"]
    expected_check = details.get("check_name") or details.get("workflow_job")
    for item in change_control.get("ci_runs", []) if isinstance(change_control.get("ci_runs"), list) else []:
        if not isinstance(item, dict):
            continue
        if (
            item.get("provider") == details.get("provider")
            and item.get("run_id_or_url") == details.get("run_id_or_url")
            and item.get("commit_sha") == details.get("commit_sha")
            and item.get("status") == "passed"
            and item.get("scope") == details.get("scope")
            and (expected_check is None or item.get("check") == expected_check)
        ):
            return []
    return [f"{label}: successful CI evidence must match a change_control.ci_runs entry by provider, run attempt, SHA, check, status, and scope"]


def validate_gate_run_records(root: Path, schema: dict[str, object], application_id: str) -> list[str]:
    """Validate app-local v1 gate-run JSON and cross-record invariants, without mutation."""
    root = root.resolve()
    directory = root / APP_GATE_RUNS
    if not directory.exists():
        return []
    try:
        directory.resolve().relative_to(root.resolve())
    except ValueError:
        return [f"{APP_GATE_RUNS.as_posix()}: gate-run directory resolves outside the repository"]
    if directory.is_symlink() or not directory.is_dir():
        return [f"{APP_GATE_RUNS.as_posix()}: gate-run path must be a real directory inside the repository"]
    problems: list[str] = []
    contract_version = str(schema.get("properties", {}).get("contract_version", {}).get("const", "unknown"))
    records: dict[str, tuple[Path, dict[str, object]]] = {}
    gate_by_relative_path: dict[str, str] = {}
    for path in sorted(directory.iterdir()):
        if path.is_dir():
            problems.append(f"{path.relative_to(root).as_posix()}: nested gate-run directories are not supported")
            continue
        if path.suffix.lower() != ".json":
            problems.append(f"{path.relative_to(root).as_posix()}: gate-run directory may contain only .json run records")
            continue
        relative = path.relative_to(root).as_posix()
        safe_path, safe_error = safe_file(root, relative)
        if safe_error or safe_path is None:
            problems.append(f"{relative}: {safe_error or 'could not resolve gate-run file'}")
            continue
        record, parse_error = load_json_object(safe_path)
        if parse_error or record is None:
            problems.append(f"{relative}: invalid gate-run JSON: {parse_error or 'invalid object'}")
            continue
        declared_gate = record.get("gate_id")
        gate_by_relative_path[relative] = declared_gate if isinstance(declared_gate, str) else "unknown-gate"
        schema_errors = validate_schema_value(record, schema, schema)
        problems.extend(f"{relative}: {problem}" for problem in schema_errors)
        if schema_errors:
            continue
        record_id = record.get("record_id")
        if not isinstance(record_id, str):
            continue
        if path.stem != record_id:
            problems.append(f"{relative}: filename stem must equal record_id '{record_id}'")
        if record_id in records:
            problems.append(f"{relative}: duplicate gate-run record_id '{record_id}'")
            continue
        records[record_id] = (safe_path, record)
        if record.get("application_id") != application_id:
            problems.append(f"{relative}: application_id does not match the app mission artifact identity '{application_id}'")

    for record_id, (path, record) in records.items():
        relative = path.relative_to(root).as_posix()
        gate_id = record.get("gate_id")
        if gate_id not in GATE_CRITERIA:
            continue
        source_snapshot = record.get("source_snapshot", {})
        source_commit = source_snapshot.get("commit_sha") if isinstance(source_snapshot, dict) else None
        results = record.get("criteria_results", [])
        criterion_ids = [item.get("criterion_id") for item in results if isinstance(item, dict)]
        if len(criterion_ids) != len(set(criterion_ids)):
            problems.append(f"{relative}: criterion IDs must be unique within a gate run")
        expected = set(GATE_CRITERIA[gate_id])
        actual = set(criterion_ids)
        for missing in sorted(expected - actual):
            problems.append(f"{relative}: required criterion {missing} is missing")
        for extra in sorted(actual - expected):
            problems.append(f"{relative}: criterion {extra} is not defined for {gate_id} by contract v{contract_version}")

        # Gate-run and evidence identity is relational; JSON Schema alone cannot resolve these references.
        evidence = record.get("evidence", [])
        evidence_by_id = {item.get("evidence_id"): item for item in evidence if isinstance(item, dict)}
        expected_scope_hash = json_sha256(record.get("scope"))
        findings = record.get("findings", [])
        finding_ids = {item.get("finding_id") for item in findings if isinstance(item, dict)}
        decisions = record.get("authority", {}).get("owner_decisions", []) if isinstance(record.get("authority"), dict) else []
        decision_ids = {item.get("decision_id") for item in decisions if isinstance(item, dict)}
        owner = record.get("authority", {}).get("accountable_owner", {}) if isinstance(record.get("authority"), dict) else {}
        owner_identity = owner.get("identity") if isinstance(owner, dict) else None
        for item in results:
            if not isinstance(item, dict):
                continue
            cid = item.get("criterion_id")
            for eid in item.get("evidence_ids", []):
                ref = evidence_by_id.get(eid)
                if ref is None:
                    problems.append(f"{relative}: criterion {cid} references unknown evidence ID '{eid}'")
                elif cid not in ref.get("criterion_ids", []):
                    problems.append(f"{relative}: evidence '{eid}' does not declare criterion {cid} in criterion_ids")
            for fid in item.get("finding_ids", []):
                if fid not in finding_ids:
                    problems.append(f"{relative}: criterion {cid} references unknown finding ID '{fid}'")
            for did in item.get("owner_decision_ids", []):
                if did not in decision_ids:
                    problems.append(f"{relative}: criterion {cid} references unknown owner decision ID '{did}'")
                elif item.get("outcome") == "not-applicable":
                    decision = next((decision for decision in decisions if isinstance(decision, dict) and decision.get("decision_id") == did), None)
                    if decision is not None and decision.get("decision_maker") != owner_identity:
                        problems.append(f"{relative}: criterion {cid} not-applicable decision '{did}' was not made by the accountable owner")
            outcome = item.get("outcome")
            if outcome == "pass" and not item.get("evidence_ids"):
                problems.append(f"{relative}: passing criterion {cid} requires at least one linked evidence record")
            if outcome == "not-applicable" and not item.get("owner_decision_ids"):
                problems.append(f"{relative}: not-applicable criterion {cid} requires an authorized owner decision reference")
        for ev in evidence:
            if not isinstance(ev, dict):
                continue
            eid = ev.get("evidence_id")
            for cid in ev.get("criterion_ids", []):
                matching = next((item for item in results if isinstance(item, dict) and item.get("criterion_id") == cid), None)
                if matching is None or eid not in matching.get("evidence_ids", []):
                    problems.append(f"{relative}: evidence '{eid}' is not reciprocally linked from criterion {cid}")
            if ev.get("source_revision") != record.get("source_snapshot", {}).get("commit_sha"):
                problems.append(f"{relative}: evidence '{eid}' source_revision does not match the gate run source snapshot")
            if contract_version in {"1.1", "1.2"} and ev.get("scope_ref") != expected_scope_hash:
                problems.append(f"{relative}: evidence '{eid}' scope_ref does not match the canonical hash of this gate run scope")
            if ev.get("type") == "artifact-reference":
                detail = ev.get("details", {})
                if source_commit is None and not any(
                    isinstance(frozen, dict) and frozen.get("path") == detail.get("path") and frozen.get("sha256") == detail.get("sha256")
                    for frozen in source_snapshot.get("files", [])
                ):
                    problems.append(f"{relative}: archive-pinned evidence artifact '{detail.get('path')}' is absent from the source snapshot digest list")
                problems.extend(_check_gate_artifact_ref(root, {
                    "artifact_id": detail.get("artifact_id"), "version": detail.get("version"),
                    "path": detail.get("path"), "sha256": detail.get("sha256"),
                    "source_revision": ev.get("source_revision"),
                }, f"{relative} evidence {eid}", records))
                evidence_path = detail.get("path")
                if ev.get("locator") != evidence_path:
                    problems.append(f"{relative}: artifact-reference evidence '{eid}' locator must equal details.path")
                evidence_file, evidence_error = safe_file(root, evidence_path) if isinstance(evidence_path, str) else (None, "path must be a string")
                if evidence_file and ev.get("record_sha256") != file_sha256(evidence_file):
                    problems.append(f"{relative}: artifact-reference evidence '{eid}' record_sha256 is stale")
                elif evidence_error:
                    problems.append(f"{relative}: artifact-reference evidence '{eid}' path is invalid: {evidence_error}")
            if ev.get("type") == "command-execution":
                detail = ev.get("details", {})
                if contract_version in {"1.1", "1.2"} and detail.get("scope") != ev.get("scope_ref"):
                    problems.append(f"{relative}: command evidence '{eid}' detail scope does not match its scope_ref")
                if not detail.get("stdout_ref") and not detail.get("stderr_ref"):
                    problems.append(f"{relative}: command evidence '{eid}' requires durable stdout_ref or stderr_ref evidence")
                for output_ref in (detail.get("stdout_ref"), detail.get("stderr_ref")):
                    if output_ref is not None:
                        output_path, output_error = safe_file(root, output_ref) if isinstance(output_ref, str) else (None, "path must be a string")
                        if output_error or output_path is None:
                            problems.append(f"{relative}: command evidence '{eid}' output reference is invalid: {output_error or 'file is missing'}")
                if detail.get("exit_code") != 0 and any(
                    isinstance(item, dict) and item.get("outcome") == "pass" and eid in item.get("evidence_ids", [])
                    for item in results
                ):
                    problems.append(f"{relative}: non-zero command evidence '{eid}' cannot support a passing criterion")
            if ev.get("type") == "ci-run":
                detail = ev.get("details", {})
                if detail.get("commit_sha") != source_commit:
                    problems.append(f"{relative}: CI evidence '{eid}' commit_sha does not match the gate-run source snapshot")
                if contract_version in {"1.1", "1.2"} and detail.get("scope") != ev.get("scope_ref"):
                    problems.append(f"{relative}: CI evidence '{eid}' detail scope does not match its scope_ref")
                if any(
                    isinstance(item, dict) and item.get("outcome") == "pass" and eid in item.get("evidence_ids", [])
                    for item in results
                ) and detail.get("conclusion") != "success":
                    problems.append(f"{relative}: CI evidence '{eid}' with a non-success conclusion cannot support a passing criterion")

        if record.get("gate_result") == "passed":
            open_blockers = [finding.get("finding_id") for finding in findings if isinstance(finding, dict) and finding.get("blocking") is True and finding.get("disposition") not in {"fixed", "not-applicable"}]
            if open_blockers:
                problems.append(f"{relative}: passed gate retains unresolved blocking finding(s): {', '.join(str(value) for value in open_blockers)}")

        result = record.get("gate_result")
        outcomes = [item.get("outcome") for item in results if isinstance(item, dict)]
        if result == "passed" and any(outcome not in {"pass", "not-applicable"} for outcome in outcomes):
            problems.append(f"{relative}: passed gate requires every criterion to pass or be not-applicable")
        if result == "passed-with-accepted-risk":
            accepted = record.get("accepted_risk")
            if not isinstance(accepted, dict):
                problems.append(f"{relative}: passed-with-accepted-risk requires accepted_risk details")
            else:
                owner_decision = next((decision for decision in decisions if isinstance(decision, dict) and decision.get("decision_id") == accepted.get("owner_decision_id")), None)
                if owner_decision is None:
                    problems.append(f"{relative}: accepted_risk owner_decision_id does not resolve")
                elif owner_decision.get("decision_maker") != owner_identity:
                    problems.append(f"{relative}: accepted_risk decision must be made by the accountable owner")
                for fid in accepted.get("finding_ids", []):
                    match = next((item for item in findings if isinstance(item, dict) and item.get("finding_id") == fid), None)
                    if match is None or match.get("blocking") is not False or match.get("disposition") != "accepted-risk":
                        problems.append(f"{relative}: accepted-risk finding '{fid}' must exist, be nonblocking, and have accepted-risk disposition")
            if any(outcome in {"fail", "blocked", "not-checked"} for outcome in outcomes):
                problems.append(f"{relative}: accepted risk cannot clear failed, blocked, or unassessed criteria")
        if result == "not-ready" and any(outcome != "not-checked" for outcome in outcomes):
            problems.append(f"{relative}: not-ready gate requires all criteria to remain not-checked")
        if result == "not-applicable" and any(outcome != "not-applicable" for outcome in outcomes):
            problems.append(f"{relative}: not-applicable gate requires every criterion to be not-applicable")
        if result == "failed" and "fail" not in outcomes:
            problems.append(f"{relative}: failed gate requires at least one failed criterion")
        if result == "blocked" and "blocked" not in outcomes:
            problems.append(f"{relative}: blocked gate requires at least one blocked criterion")

        if isinstance(source_snapshot, dict):
            commit_sha = source_snapshot.get("commit_sha")
            revision_state = source_snapshot.get("revision_state")
            if revision_state == "clean-commit" and not isinstance(commit_sha, str):
                problems.append(f"{relative}: clean-commit source snapshot requires commit_sha")
            if commit_sha is None:
                snapshot_files = source_snapshot.get("files", [])
                archive_snapshot_complete = revision_state == "archive-pinned" and bool(source_snapshot.get("uncommitted_reason")) and bool(snapshot_files)
                initial_not_ready = revision_state == "not-yet-initialized" and result == "not-ready" and not snapshot_files
                if not archive_snapshot_complete and not initial_not_ready:
                    problems.append(f"{relative}: a null commit_sha requires a digest-complete archive-pinned snapshot or an empty not-yet-initialized not-ready record")
            if revision_state in {"dirty-working-tree", "not-yet-initialized"} and result in {"passed", "passed-with-accepted-risk"} and gate_id in {"G-IMPL", "G-RELEASE"}:
                problems.append(f"{relative}: {gate_id} cannot pass from a dirty or uninitialized source snapshot")
            for ref in source_snapshot.get("files", []):
                problems.extend(_check_gate_artifact_ref(root, ref, f"{relative} source_snapshot.files", records))
                if isinstance(ref, dict) and ref.get("source_revision") != commit_sha:
                    problems.append(f"{relative}: source_snapshot file '{ref.get('path')}' revision does not match commit_sha")
        scope = record.get("scope", {})
        if isinstance(scope, dict):
            refs = scope.get("artifact_refs", [])
            for ref in refs:
                problems.extend(_check_gate_artifact_ref(root, ref, f"{relative} scope.artifact_refs", records))
                if isinstance(ref, dict) and not ref.get("path", "").startswith(APP_GATE_RUNS.as_posix() + "/"):
                    if ref.get("source_revision") != source_commit:
                        problems.append(f"{relative}: scope artifact '{ref.get('path')}' source_revision does not match the gate-run source snapshot")
                    if source_commit is None and not any(
                        isinstance(frozen, dict) and frozen.get("path") == ref.get("path") and frozen.get("sha256") == ref.get("sha256")
                        for frozen in source_snapshot.get("files", [])
                    ):
                        problems.append(f"{relative}: archive-pinned scope artifact '{ref.get('path')}' is absent from the source snapshot digest list")
            for exclusion in scope.get("exclusions", []):
                if isinstance(exclusion, dict) and exclusion.get("authority") in (None, ""):
                    problems.append(f"{relative}: scope exclusion '{exclusion.get('item')}' requires decision authority")
            for requirement_id in scope.get("requirement_ids", []):
                if not _id_occurs_in_paths(root, requirement_id, ("specification.md",)):
                    problems.append(f"{relative}: scope requirement ID '{requirement_id}' does not resolve in specification.md")
            for task_id in scope.get("task_ids", []):
                if not _id_occurs_in_paths(root, task_id, ("backlog.md",)):
                    problems.append(f"{relative}: scope task ID '{task_id}' does not resolve in backlog.md")
            for requirement_id in scope.get("requirement_ids", []):
                if not _id_occurs_in_paths(root, requirement_id, ("specification.md",)):
                    problems.append(f"{relative}: scope requirement ID '{requirement_id}' does not resolve in specification.md")
            for task_id in scope.get("task_ids", []):
                if not _id_occurs_in_paths(root, task_id, ("backlog.md",)):
                    problems.append(f"{relative}: scope task ID '{task_id}' does not resolve in backlog.md")

        if gate_id == "G-FEAS":
            gate_data = record.get("gate_data", {})
            probes = gate_data.get("probes", []) if isinstance(gate_data, dict) else []
            scoped_requirements = set(scope.get("requirement_ids", [])) if isinstance(scope, dict) else set()
            scoped_tasks = set(scope.get("task_ids", [])) if isinstance(scope, dict) else set()
            covered_requirements: set[str] = set()
            covered_tasks: set[str] = set()
            probe_dependencies: dict[str, dict[str, object]] = {}
            for probe in probes:
                if not isinstance(probe, dict):
                    continue
                covered_requirements.update(probe.get("requirement_ids", []))
                classification = probe.get("classification")
                task_dependencies = probe.get("task_dependencies", [])
                for dependency in task_dependencies:
                    if not isinstance(dependency, dict):
                        continue
                    task_id = dependency.get("task_id")
                    covered_tasks.add(task_id)
                    if task_id in probe_dependencies and probe_dependencies[task_id] != dependency:
                        problems.append(f"{relative}: feasibility task '{task_id}' has conflicting probe dependency states")
                    probe_dependencies[task_id] = dependency
                    if isinstance(scope, dict) and task_id not in scope.get("task_ids", []):
                        problems.append(f"{relative}: feasibility dependency task '{task_id}' is not declared in scope.task_ids")
                    state = dependency.get("state")
                    if classification in {"unknown", "unsupported", "constrained"} and state == "unblocked":
                        problems.append(f"{relative}: {classification} feasibility probe '{probe.get('probe_id')}' cannot leave task '{task_id}' unconditionally unblocked")
                    if state == "conditional":
                        for field in ("condition", "safe_work_boundary"):
                            if not isinstance(dependency.get(field), str) or not dependency[field].strip():
                                problems.append(f"{relative}: conditional feasibility task '{task_id}' requires {field}")
                        if contract_version in {"1.1", "1.2"} and (not isinstance(dependency.get("state_change_trigger"), str) or not dependency["state_change_trigger"].strip()):
                            problems.append(f"{relative}: conditional feasibility task '{task_id}' requires state_change_trigger")
                for requirement_id in probe.get("requirement_ids", []):
                    if isinstance(scope, dict) and requirement_id not in scoped_requirements:
                        problems.append(f"{relative}: feasibility probe '{probe.get('probe_id')}' references out-of-scope requirement '{requirement_id}'")
            for requirement_id in sorted(scoped_requirements - covered_requirements):
                problems.append(f"{relative}: G-FEAS scope requirement '{requirement_id}' has no feasibility probe classification")
            for task_id in sorted(scoped_tasks - covered_tasks):
                problems.append(f"{relative}: G-FEAS scoped task '{task_id}' has no probe dependency state")
            effects = record.get("dependency_effects", [])
            effect_by_task = {effect.get("task_id"): effect for effect in effects if isinstance(effect, dict)}
            for task_id, dependency in probe_dependencies.items():
                effect = effect_by_task.get(task_id)
                if effect is None:
                    problems.append(f"{relative}: feasibility task '{task_id}' has no matching dependency_effect")
                    continue
                for field in ("state", "condition", "safe_work_boundary"):
                    if effect.get(field) != dependency.get(field):
                        problems.append(f"{relative}: feasibility task '{task_id}' dependency_effect {field} does not match its probe")
                if contract_version in {"1.1", "1.2"} and effect.get("state_change_trigger") != dependency.get("state_change_trigger"):
                    problems.append(f"{relative}: feasibility task '{task_id}' dependency_effect state_change_trigger does not match its probe")
            for task_id in effect_by_task.keys() - probe_dependencies.keys():
                problems.append(f"{relative}: dependency_effect task '{task_id}' has no matching feasibility probe dependency")
            for effect in effects:
                if isinstance(effect, dict) and effect.get("state") == "conditional":
                    task_id = effect.get("task_id")
                    for field in ("condition", "safe_work_boundary"):
                        if not isinstance(effect.get(field), str) or not effect[field].strip():
                            problems.append(f"{relative}: conditional dependency effect '{task_id}' requires {field}")
                    if contract_version in {"1.1", "1.2"} and (not isinstance(effect.get("state_change_trigger"), str) or not effect["state_change_trigger"].strip()):
                        problems.append(f"{relative}: conditional dependency effect '{task_id}' requires state_change_trigger")

        # Gate profile evidence IDs must resolve to evidence records of the declared type.
        gate_data = record.get("gate_data", {})
        if isinstance(gate_data, dict):
            if gate_id == "G-INTENT" and record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                mission_id = f"{application_id}-MISSION-001"
                mission_evidence = next((
                    item for item in evidence
                    if isinstance(item, dict)
                    and item.get("type") == "artifact-reference"
                    and isinstance(item.get("details"), dict)
                    and item["details"].get("artifact_id") == mission_id
                    and item["details"].get("path") == "mission.md"
                ), None)
                mission_path = root / "mission.md"
                mission_digest = file_sha256(mission_path) if mission_path.is_file() else None
                if mission_evidence is None:
                    problems.append(f"{relative}: passed G-INTENT requires artifact-reference evidence for the current mission.md")
                exclusions = record.get("scope", {}).get("exclusions", []) if isinstance(record.get("scope"), dict) else []
                mission_text = mission_path.read_text(encoding="utf-8") if mission_path.is_file() else ""
                exclusion_items = [item.get("item") for item in exclusions if isinstance(item, dict)] if isinstance(exclusions, list) else []
                if not exclusion_items or not any(isinstance(item, str) and item.strip() for item in exclusion_items):
                    problems.append(f"{relative}: passed G-INTENT requires explicit negative-space scope.exclusions")
                else:
                    for exclusion in exclusion_items:
                        if not isinstance(exclusion, str) or not exclusion.strip() or exclusion.casefold() not in mission_text.casefold():
                            problems.append(f"{relative}: passed G-INTENT exclusion must be stated in the current mission.md")
                approval = next((
                    decision for decision in decisions
                    if isinstance(decision, dict)
                    and decision.get("decision_maker") == owner_identity
                    and decision.get("choice") == f"approve-intent: {mission_id}; digest={mission_digest}"
                    and mission_id in decision.get("affected_ids", [])
                ), None)
                if approval is None:
                    problems.append(f"{relative}: passed G-INTENT requires accountable-owner approval bound to mission ID and exact mission digest")
                for criterion in results:
                    if not isinstance(criterion, dict):
                        continue
                    if mission_evidence is not None and mission_evidence.get("evidence_id") not in criterion.get("evidence_ids", []):
                        problems.append(f"{relative}: passed G-INTENT criterion {criterion.get('criterion_id')} must link current mission artifact evidence")
                    if approval is not None and approval.get("decision_id") not in criterion.get("owner_decision_ids", []):
                        problems.append(f"{relative}: passed G-INTENT criterion {criterion.get('criterion_id')} must link the exact owner mission approval")
            for requirement_id in gate_data.get("requirement_ids", []):
                if not _id_occurs_in_paths(root, requirement_id, ("specification.md",)):
                    problems.append(f"{relative}: gate_data requirement ID '{requirement_id}' does not resolve in specification.md")
            for decision_id in gate_data.get("decision_ids", []):
                if not _id_occurs_in_paths(root, decision_id, ("decisions",)):
                    problems.append(f"{relative}: gate_data decision ID '{decision_id}' does not resolve in decisions/")
            for task_id in gate_data.get("backlog_task_ids", []):
                if not _id_occurs_in_paths(root, task_id, ("backlog.md",)):
                    problems.append(f"{relative}: gate_data backlog task ID '{task_id}' does not resolve in backlog.md")
            if gate_id == "G-COVERAGE":
                if record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                    applicability = gate_data.get("failure_mode_applicability", [])
                    if not any(isinstance(row, dict) and row.get("applicable") is True for row in applicability):
                        problems.append(f"{relative}: passed G-COVERAGE requires at least one applicable failure-mode row; a happy-path-only matrix cannot pass")
                scope_surfaces = set(scope.get("surfaces", [])) if isinstance(scope, dict) else set()
                scope_platforms = set(scope.get("platforms", [])) if isinstance(scope, dict) else set()
                applicability = gate_data.get("platform_applicability", [])
                mapped_surfaces = {row.get("surface") for row in applicability if isinstance(row, dict)}
                mapped_platforms = {row.get("platform") for row in applicability if isinstance(row, dict)}
                for surface in sorted(scope_surfaces - mapped_surfaces):
                    problems.append(f"{relative}: G-COVERAGE scope surface '{surface}' has no platform_applicability row")
                for surface in sorted(mapped_surfaces - scope_surfaces):
                    problems.append(f"{relative}: G-COVERAGE platform_applicability surface '{surface}' is outside scope.surfaces")
                for platform in sorted(scope_platforms - mapped_platforms):
                    problems.append(f"{relative}: G-COVERAGE scope platform '{platform}' has no platform_applicability row")
                for platform in sorted(mapped_platforms - scope_platforms):
                    problems.append(f"{relative}: G-COVERAGE platform_applicability platform '{platform}' is outside scope.platforms")
                pairs = [(row.get("surface"), row.get("platform")) for row in applicability if isinstance(row, dict)]
                if len(pairs) != len(set(pairs)):
                    problems.append(f"{relative}: G-COVERAGE platform_applicability must not duplicate a surface/platform pair")
                for journey in gate_data.get("journeys", []):
                    if not isinstance(journey, dict):
                        continue
                    for requirement_id in journey.get("requirement_ids", []):
                        if requirement_id not in scope.get("requirement_ids", []):
                            problems.append(f"{relative}: journey '{journey.get('journey_id')}' references out-of-scope requirement '{requirement_id}'")
        if isinstance(gate_data, dict):
            for requirement_id in gate_data.get("requirement_ids", []):
                if not _id_occurs_in_paths(root, requirement_id, ("specification.md",)):
                    problems.append(f"{relative}: gate_data requirement ID '{requirement_id}' does not resolve in specification.md")
            for decision_id in gate_data.get("decision_ids", []):
                if not _id_occurs_in_paths(root, decision_id, ("decisions",)):
                    problems.append(f"{relative}: gate_data decision ID '{decision_id}' does not resolve in decisions/")
            for task_id in gate_data.get("backlog_task_ids", []):
                if not _id_occurs_in_paths(root, task_id, ("backlog.md",)):
                    problems.append(f"{relative}: gate_data backlog task ID '{task_id}' does not resolve in backlog.md")
            if gate_id == "G-COVERAGE":
                for journey in gate_data.get("journeys", []):
                    if not isinstance(journey, dict):
                        continue
                    for requirement_id in journey.get("requirement_ids", []):
                        if requirement_id not in scope.get("requirement_ids", []):
                            problems.append(f"{relative}: journey '{journey.get('journey_id')}' references out-of-scope requirement '{requirement_id}'")
        evidence_field_types = {
            "cold_start_evidence_ids": {"command-execution", "ci-run"},
            "interaction_evidence_ids": {"interaction-capture", "manual-observation"},
            "review_evidence_ids": {"review-finding"},
            "runbook_evidence_ids": {"operational-record", "manual-observation", "command-execution"},
        }
        if isinstance(gate_data, dict):
            for field, allowed_types in evidence_field_types.items():
                if field not in gate_data:
                    continue
                if not isinstance(gate_data[field], list):
                    continue
                for evidence_id in gate_data[field]:
                    item = evidence_by_id.get(evidence_id)
                    if item is None:
                        problems.append(f"{relative}: gate_data.{field} references unknown evidence ID '{evidence_id}'")
                    elif item.get("type") not in allowed_types:
                        problems.append(f"{relative}: evidence '{evidence_id}' has type '{item.get('type')}', not allowed for gate_data.{field}")
            if record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                required_evidence_fields = {
                    "G-SETUP": ("cold_start_evidence_ids",),
                    "G-REQ": ("review_evidence_ids",),
                    "G-CX": ("interaction_evidence_ids",),
                    "G-IMPL": ("review_evidence_ids",),
                    "G-RELEASE": ("required_check_evidence_ids", "security_accessibility_platform_evidence_ids"),
                    "G-OPERATE": ("runbook_evidence_ids",),
                }.get(gate_id, ())
                for field in required_evidence_fields:
                    if not gate_data.get(field):
                        problems.append(f"{relative}: {gate_id} PASS requires non-empty gate_data.{field}")
            if gate_id == "G-IMPL":
                selected_task = gate_data.get("selected_task_id")
                if isinstance(scope, dict) and selected_task not in scope.get("task_ids", []):
                    problems.append(f"{relative}: G-IMPL selected_task_id must be present in scope.task_ids")
                if record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                    change_control = record.get("change_control", {})
                    authority = record.get("authority", {})
                    problems.extend(_published_checkpoint_problems(change_control, source_commit, authority, [selected_task], f"{relative} G-IMPL"))
                    mappings = gate_data.get("criterion_check_mappings", [])
                    mapping_ids = [item.get("criterion_id") for item in mappings if isinstance(item, dict)]
                    if len(mapping_ids) != len(set(mapping_ids)) or set(mapping_ids) != set(GATE_CRITERIA[gate_id]):
                        problems.append(f"{relative}: passing G-IMPL requires exactly one check/manual mapping per GIMPL criterion")
                    checks = gate_data.get("required_checks", [])
                    checks_by_id = {item.get("check_id"): item for item in checks if isinstance(item, dict)}
                    if len(checks_by_id) != len(checks):
                        problems.append(f"{relative}: passing G-IMPL must use unique required check IDs")
                    app_lock, _ = load_json_object(root / APP_FRAMEWORK_LOCK)
                    if app_lock and app_lock.get("lock_version") in {3, 4}:
                        manifest, manifest_problems = required_check_manifest(root)
                        problems.extend(manifest_problems)
                        if manifest is not None:
                            applicable = [
                                item for item in manifest.get("checks", [])
                                if isinstance(item, dict) and item.get("required") is True
                                and selected_task in item.get("task_ids", [])
                            ]
                            if manifest.get("status") != "active" or not applicable:
                                problems.append(f"{relative}: passing G-IMPL requires an active required-check manifest with checks for selected task '{selected_task}'")
                            for declared in applicable:
                                check_id = declared.get("check_id")
                                if declared.get("execution") == "ci":
                                    observed = checks_by_id.get(check_id)
                                    if observed is None:
                                        problems.append(f"{relative}: passing G-IMPL omits manifest-required check '{check_id}'")
                                    elif observed.get("command_or_procedure") != declared.get("command_or_procedure"):
                                        problems.append(f"{relative}: G-IMPL check '{check_id}' command differs from the required-check manifest")
                                    elif observed.get("pass_condition") != declared.get("pass_condition"):
                                        problems.append(f"{relative}: G-IMPL check '{check_id}' pass condition differs from the required-check manifest")
                                    elif observed.get("scope") != ", ".join(sorted(declared.get("scope_paths", []))):
                                        problems.append(f"{relative}: G-IMPL check '{check_id}' scope must match the manifest scope_paths joined in sorted order")
                                elif declared.get("execution") == "manual" and not any(
                                    isinstance(mapping, dict) and isinstance(mapping.get("manual_method"), str)
                                    and check_id in mapping["manual_method"]
                                    for mapping in mappings
                                ):
                                    problems.append(f"{relative}: G-IMPL criterion mappings must identify required manual check '{check_id}' in manual_method")
                            if app_lock.get("lock_version") == 4:
                                expected_check_ids = {item.get("check_id") for item in applicable}
                                if set(checks_by_id) != expected_check_ids:
                                    problems.append(f"{relative}: lock-v4 G-IMPL required_checks must exactly match the manifest-required checks for selected task '{selected_task}'")
                                if record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                                    trusted_policy, trust_problems = trusted_ci_policy(root)
                                    problems.extend(f"{relative}: {problem}" for problem in trust_problems)
                                    if trusted_policy is None or trusted_policy.get("status") != "active":
                                        problems.append(f"{relative}: lock-v4 G-IMPL PASS requires an active trusted CI policy")
                                    else:
                                        verified_evidence_ids: set[str] = set()
                                        for observed_check in checks:
                                            if not isinstance(observed_check, dict):
                                                continue
                                            evidence_id = observed_check.get("evidence_id")
                                            if not isinstance(evidence_id, str) or evidence_id in verified_evidence_ids:
                                                continue
                                            verified_evidence_ids.add(evidence_id)
                                            linked_evidence = evidence_by_id.get(evidence_id)
                                            if linked_evidence is None:
                                                continue
                                            evidence_type_problem = _lock_v4_gimpl_evidence_type_problem(
                                                linked_evidence, f"{relative} evidence '{evidence_id}'",
                                            )
                                            if evidence_type_problem:
                                                problems.append(evidence_type_problem)
                                                continue
                                            problems.extend(_trusted_gimpl_attestation_problems(
                                                root, record, linked_evidence, source_commit, trusted_policy,
                                                [item for item in applicable if isinstance(item, dict)],
                                                f"{relative} evidence '{evidence_id}'",
                                            ))
                    for mapping in mappings:
                        if not isinstance(mapping, dict):
                            continue
                        if not mapping.get("check_ids") and not (isinstance(mapping.get("manual_method"), str) and mapping["manual_method"].strip()):
                            problems.append(f"{relative}: G-IMPL criterion mapping '{mapping.get('criterion_id')}' requires check_ids or a manual_method")
                        for check_id in mapping.get("check_ids", []):
                            if check_id not in checks_by_id:
                                problems.append(f"{relative}: G-IMPL criterion '{mapping.get('criterion_id')}' references unknown check_id '{check_id}'")
                    for check in checks:
                        if not isinstance(check, dict):
                            continue
                        check_id = check.get("check_id")
                        if check.get("source_revision") != source_commit:
                            problems.append(f"{relative}: required check '{check_id}' source_revision does not match the gate-run snapshot")
                        evidence_id = check.get("evidence_id")
                        ev = evidence_by_id.get(evidence_id)
                        if check.get("result") != "passed" or ev is None:
                            problems.append(f"{relative}: required check '{check_id}' must have passed with linked execution/CI evidence")
                        elif ev.get("type") not in {"command-execution", "ci-run"}:
                            problems.append(f"{relative}: required check '{check_id}' evidence must be command-execution or ci-run")
                        elif ev.get("type") == "ci-run" and isinstance(ev.get("details"), dict) and ev["details"].get("commit_sha") != source_commit:
                            problems.append(f"{relative}: required CI check '{check_id}' commit does not match the gate-run snapshot")
                        elif ev.get("type") == "ci-run" and isinstance(ev.get("details"), dict) and ev["details"].get("conclusion") != "success":
                            problems.append(f"{relative}: required CI check '{check_id}' evidence conclusion must be success")
                        elif ev is not None and ev.get("type") == "ci-run":
                            problems.extend(_ci_change_control_reference_problems(change_control, ev, f"{relative} required CI check '{check_id}'"))
                        elif ev.get("type") == "command-execution" and isinstance(ev.get("details"), dict) and ev["details"].get("exit_code") != 0:
                            problems.append(f"{relative}: required command check '{check_id}' did not exit successfully")
                        if ev is not None and isinstance(ev.get("details"), dict):
                            details = ev["details"]
                            if check.get("scope") != details.get("scope"):
                                problems.append(f"{relative}: required check '{check_id}' scope does not match linked evidence")
                            observed_command = details.get("command_or_procedure") or details.get("command") or details.get("check_name") or details.get("workflow_job")
                            if check.get("command_or_procedure") != observed_command:
                                problems.append(f"{relative}: required check '{check_id}' command_or_procedure does not match linked evidence")
                            runtimes = details.get("runtime_versions", [])
                            if check.get("tool_runtime_version") not in runtimes and check.get("tool_runtime_version") != details.get("tool_runtime_version"):
                                problems.append(f"{relative}: required check '{check_id}' tool_runtime_version does not match linked evidence")
                            observed_pass_condition = details.get("pass_condition")
                            if observed_pass_condition is None and ev.get("type") == "command-execution" and details.get("exit_code") == 0:
                                observed_pass_condition = "exit_code == 0"
                            if observed_pass_condition is None and ev.get("type") == "ci-run" and details.get("conclusion") == "success":
                                observed_pass_condition = "conclusion == success"
                            if check.get("pass_condition") != observed_pass_condition:
                                problems.append(f"{relative}: required check '{check_id}' pass_condition does not match linked evidence")
            if gate_id in {"G-REQ", "G-ARCH"} and record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                lock, lock_error = load_json_object(root / APP_FRAMEWORK_LOCK)
                if lock_error or lock is None:
                    problems.append(f"{relative}: passed {gate_id} run requires a valid framework lock")
                else:
                    framework_revision = lock.get("framework_revision")
                    if not isinstance(framework_revision, str):
                        problems.append(f"{relative}: passed {gate_id} run requires a pinned framework revision")
                    else:
                        problems.extend(validate_handoff_manifest(root, gate_id, framework_revision))
                if gate_id == "G-REQ":
                    reviewers = record.get("authority", {}).get("reviewers", [])
                    if not _has_independent_reviewer(reviewers):
                        problems.append(f"{relative}: passed G-REQ requires an independent reviewer result, context disclosure, and author_overlap 'none'")
            if gate_id == "G-ARCH" and record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                verification_contracts = gate_data.get("verification_contracts", [])
                if not verification_contracts:
                    problems.append(f"{relative}: passed G-ARCH requires at least one verified contract with linked evidence; prose assertions alone cannot pass")
                for contract in verification_contracts:
                    if not isinstance(contract, dict) or not isinstance(contract.get("evidence_id"), str) or contract.get("evidence_id") not in evidence_by_id:
                        problems.append(f"{relative}: passed G-ARCH verification contract must link a resolvable evidence record")
                    elif evidence_by_id[contract["evidence_id"]].get("type") not in {"command-execution", "ci-run"}:
                        problems.append(f"{relative}: passed G-ARCH verification contract requires command-execution or ci-run evidence; narrative observations cannot verify a data/security contract")
                reviewers = record.get("authority", {}).get("reviewers", [])
                if not _has_independent_reviewer(reviewers):
                    problems.append(f"{relative}: passed G-ARCH requires an independent reviewer result, context disclosure, and author_overlap 'none'")
            if gate_id == "G-OPERATE" and record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                telemetry_gaps = gate_data.get("telemetry_gaps", [])
                if not telemetry_gaps or not any(isinstance(item, str) and item.strip() for item in telemetry_gaps):
                    problems.append(f"{relative}: passed G-OPERATE requires an explicit telemetry_gaps declaration; use an explicit none-known statement when applicable")
            if gate_id == "G-RELEASE":
                change = record.get("change_control", {})
                if not isinstance(change, dict):
                    change = {}
                if record.get("gate_result") in {"passed", "passed-with-accepted-risk"}:
                    authority = record.get("authority", {})
                    problems.extend(_published_checkpoint_problems(change, source_commit, authority, scope.get("task_ids", []) if isinstance(scope, dict) else [], f"{relative} G-RELEASE"))
                    if change.get("authorization_ref") != gate_data.get("owner_authorization_id"):
                        problems.append(f"{relative}: G-RELEASE publication authorization_ref must match gate_data.owner_authorization_id")
                    if gate_data.get("tested_commit_sha") != change.get("commit_sha"):
                        problems.append(f"{relative}: G-RELEASE tested_commit_sha must match change_control.commit_sha")
                    if gate_data.get("tested_commit_sha") != source_commit:
                        problems.append(f"{relative}: G-RELEASE tested_commit_sha must match the gate-run source snapshot")
                    if gate_data.get("artifact_sha256") != change.get("release_artifact_sha256"):
                        problems.append(f"{relative}: G-RELEASE artifact digest must match change_control.release_artifact_sha256")
                    authorization = next((decision for decision in decisions if isinstance(decision, dict) and decision.get("decision_id") == gate_data.get("owner_authorization_id")), None)
                    if authorization is None:
                        problems.append(f"{relative}: G-RELEASE owner_authorization_id does not resolve to an owner decision")
                    else:
                        environment = gate_data.get("environment")
                        artifact_digest = gate_data.get("artifact_sha256")
                        if authorization.get("decision_maker") != owner_identity:
                            problems.append(f"{relative}: G-RELEASE authorization must be made by the accountable owner")
                        if contract_version in {"1.1", "1.2"}:
                            if authorization.get("authorized_artifact_sha256") != artifact_digest or authorization.get("authorized_environment") != environment or authorization.get("authorized_release_window") != gate_data.get("release_window"):
                                problems.append(f"{relative}: G-RELEASE authorization must exactly bind artifact digest, environment, and release window")
                            authorized_window = gate_data.get("release_window")
                        else:
                            authorized_window = authorization.get("revisit_condition")
                            expected_choice = f"authorize-release: {artifact_digest}; environment: {environment}"
                            if not isinstance(artifact_digest, str) or not isinstance(environment, str) or authorization.get("choice") != expected_choice:
                                problems.append(f"{relative}: G-RELEASE owner decision choice must exactly equal 'authorize-release: <artifact digest>; environment: <environment>'")
                        parsed_window = parse_release_window(authorized_window)
                        if parsed_window is None:
                            problems.append(f"{relative}: G-RELEASE owner authorization must define a valid 'release-window: <start>/<end>' with timezone offsets")
                        else:
                            try:
                                gate_record_time = dt.datetime.fromisoformat(record.get("created_at", "").replace("Z", "+00:00"))
                            except (AttributeError, ValueError):
                                gate_record_time = None
                            if gate_record_time is None or gate_record_time.tzinfo is None or not parsed_window[0] <= gate_record_time < parsed_window[1]:
                                problems.append(f"{relative}: G-RELEASE gate record time must fall within the owner-authorized release window")
                            try:
                                authorization_time = dt.datetime.fromisoformat(authorization.get("decided_at", "").replace("Z", "+00:00"))
                            except (AttributeError, ValueError):
                                authorization_time = None
                            if authorization_time is None or authorization_time.tzinfo is None:
                                problems.append(f"{relative}: G-RELEASE owner authorization must have a timezone-aware decision timestamp")
                            elif gate_record_time is not None and authorization_time > gate_record_time:
                                problems.append(f"{relative}: G-RELEASE owner decision must be recorded no later than the gate authorization record")
                    artifact_evidence = [item for item in evidence if isinstance(item, dict) and item.get("type") == "artifact-reference" and isinstance(item.get("details"), dict) and item["details"].get("sha256") == gate_data.get("artifact_sha256")]
                    if not artifact_evidence:
                        problems.append(f"{relative}: G-RELEASE artifact digest must resolve to artifact-reference evidence")
                for evidence_id in gate_data.get("required_check_evidence_ids", []):
                    item = evidence_by_id.get(evidence_id)
                    if item is None or item.get("type") != "ci-run" or not isinstance(item.get("details"), dict) or item["details"].get("conclusion") != "success" or item["details"].get("commit_sha") != source_commit:
                        problems.append(f"{relative}: required release check evidence '{evidence_id}' must be a successful ci-run for the exact gate-run commit")
                    elif isinstance(item.get("details"), dict):
                        problems.extend(_ci_change_control_reference_problems(change, item, f"{relative} required release check evidence '{evidence_id}'"))

    latest, transition_problems = _latest_gate_runs(records)
    problems.extend(transition_problems)
    relative_by_record_id = {
        record_id: (path.relative_to(root).as_posix(), str(record.get("gate_id", "unknown-gate")))
        for record_id, (path, record) in records.items()
    }
    diagnostics: list[str] = []
    for problem in problems:
        first, separator, remainder = problem.partition(": ")
        if separator and first in gate_by_relative_path:
            label = f"{first} [{gate_by_relative_path[first]}]"
            detail = remainder
        elif separator and first in relative_by_record_id:
            relative, gate_id = relative_by_record_id[first]
            label = f"{relative} [{gate_id}]"
            detail = remainder
        elif separator and first.startswith(APP_GATE_RUNS.as_posix() + "/"):
            label = f"{first} [gate-run]"
            detail = remainder
        else:
            label = "gate-run validation"
            detail = problem
        diagnostics.append(f"{label}: {detail}; corrective action: fix the referenced gate record, artifact, or evidence and rerun validation")
    return diagnostics


def required_check_manifest(root: Path) -> tuple[dict[str, object] | None, list[str]]:
    manifest_path, path_error = safe_file(root, APP_REQUIRED_CHECKS.as_posix())
    if path_error or manifest_path is None:
        return None, [f"{APP_REQUIRED_CHECKS.as_posix()}: {path_error or 'could not resolve manifest'}"]
    manifest, parse_error = load_json_object(manifest_path)
    if parse_error or manifest is None:
        return None, [f"{APP_REQUIRED_CHECKS.as_posix()}: invalid JSON manifest: {parse_error or 'invalid object'}"]
    schema_path, schema_error = safe_file(root, APP_REQUIRED_CHECKS_SCHEMA.as_posix())
    if schema_error or schema_path is None:
        return None, [f"{APP_REQUIRED_CHECKS_SCHEMA.as_posix()}: {schema_error or 'required schema is missing'}"]
    schema, schema_parse_error = load_json_object(schema_path)
    if schema_parse_error or schema is None:
        return None, [f"{APP_REQUIRED_CHECKS_SCHEMA.as_posix()}: invalid JSON Schema: {schema_parse_error or 'invalid object'}"]
    schema_errors = schema_definition_problems(schema)
    if schema_errors:
        return None, [f"{APP_REQUIRED_CHECKS_SCHEMA.as_posix()}: {problem}" for problem in schema_errors]
    problems = [f"{APP_REQUIRED_CHECKS.as_posix()}: {problem}" for problem in validate_schema_value(manifest, schema, schema)]
    seen: set[str] = set()
    checks = manifest.get("checks", [])
    if isinstance(checks, list):
        for index, check in enumerate(checks):
            if not isinstance(check, dict):
                continue
            check_id = check.get("check_id")
            label = f"{APP_REQUIRED_CHECKS.as_posix()} checks[{index}]"
            if isinstance(check_id, str):
                if check_id in seen:
                    problems.append(f"{label}: duplicate check_id '{check_id}'")
                seen.add(check_id)
            if check.get("execution") == "ci" and check.get("required") is True:
                command = check.get("command_or_procedure")
                if isinstance(command, str) and len(command) > 4096:
                    problems.append(f"{label}: required command exceeds the 4096-character execution limit")
            for field in ("scope_paths", "evidence_location"):
                candidates = check.get(field, []) if field == "scope_paths" else [check.get(field)]
                for value in candidates if isinstance(candidates, list) else []:
                    if not isinstance(value, str):
                        continue
                    path = Path(value)
                    if path.is_absolute() or ".." in path.parts:
                        problems.append(f"{label}: {field} path '{value}' must be repository-relative and must not contain '..'")
    return manifest, problems


def trusted_ci_policy(root: Path) -> tuple[dict[str, object] | None, list[str]]:
    policy_path, path_error = safe_file(root, APP_TRUSTED_CI.as_posix())
    if path_error or policy_path is None:
        return None, [f"{APP_TRUSTED_CI.as_posix()}: {path_error or 'could not resolve policy'}"]
    policy, parse_error = load_json_object(policy_path)
    if parse_error or policy is None:
        return None, [f"{APP_TRUSTED_CI.as_posix()}: invalid JSON policy: {parse_error or 'invalid object'}"]
    schema_path, schema_error = safe_file(root, APP_TRUSTED_CI_SCHEMA.as_posix())
    if schema_error or schema_path is None:
        return None, [f"{APP_TRUSTED_CI_SCHEMA.as_posix()}: {schema_error or 'required schema is missing'}"]
    schema, schema_parse_error = load_json_object(schema_path)
    if schema_parse_error or schema is None:
        return None, [f"{APP_TRUSTED_CI_SCHEMA.as_posix()}: invalid JSON Schema: {schema_parse_error or 'invalid object'}"]
    schema_problems = schema_definition_problems(schema)
    if schema_problems:
        return None, [f"{APP_TRUSTED_CI_SCHEMA.as_posix()}: {problem}" for problem in schema_problems]
    problems = [f"{APP_TRUSTED_CI.as_posix()}: {problem}" for problem in validate_schema_value(policy, schema, schema)]
    if policy.get("status") == "active":
        repo = policy.get("repository")
        protected_ref = policy.get("protected_ref")
        if isinstance(repo, str) and repo.lower() != repo:
            problems.append(f"{APP_TRUSTED_CI.as_posix()}: repository must use lowercase canonical owner/repository spelling")
        if isinstance(protected_ref, str):
            try:
                ref_result = subprocess.run(
                    ["git", "check-ref-format", protected_ref], cwd=root,
                    capture_output=True, check=False, timeout=5,
                )
                valid_git_ref = ref_result.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                valid_git_ref = False
            if (".." in protected_ref or "//" in protected_ref or protected_ref.endswith("/")
                    or not protected_ref.startswith("refs/heads/") or not valid_git_ref):
                problems.append(f"{APP_TRUSTED_CI.as_posix()}: protected_ref is not a valid fully qualified branch ref")
    lock, lock_error = load_json_object(root / APP_FRAMEWORK_LOCK)
    if lock_error is None and isinstance(lock, dict) and lock.get("lock_version") == 4:
        if lock.get("framework_repository") != CANONICAL_FRAMEWORK_URL:
            problems.append(
                f"{APP_FRAMEWORK_LOCK.as_posix()}: lock-v4 trusted CI requires the canonical framework repository "
                f"{CANONICAL_FRAMEWORK_URL}"
            )
        if policy.get("signer_digest") != lock.get("framework_revision"):
            problems.append(f"{APP_TRUSTED_CI.as_posix()}: signer_digest must match the immutable framework revision in {APP_FRAMEWORK_LOCK.as_posix()}")
        if policy.get("signer_workflow") != CANONICAL_ATTESTER:
            problems.append(f"{APP_TRUSTED_CI.as_posix()}: signer_workflow must be the canonical framework-owned reusable attester")
    return policy, problems


def _git_blob(root: Path, revision: str, relative: str) -> tuple[bytes | None, str | None]:
    if not FRAMEWORK_REVISION_RE.fullmatch(revision):
        return None, "source revision is not a full commit SHA"
    try:
        result = subprocess.run(
            ["git", "cat-file", "blob", f"{revision}:{relative}"],
            cwd=root, capture_output=True, check=False, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"could not read source-pinned {relative}: {exc}"
    if result.returncode != 0:
        return None, f"source commit does not contain {relative}"
    return result.stdout, None


def _lock_v4_gimpl_evidence_type_problem(evidence: dict[str, object], label: str) -> str | None:
    if evidence.get("type") != "ci-run":
        return f"{label}: lock-v4 G-IMPL PASS cannot use local/manual command evidence; a provider-attested ci-run is required"
    return None


def _trusted_gimpl_attestation_problems(
    root: Path,
    record: dict[str, object],
    evidence: dict[str, object],
    source_sha: str,
    trusted_policy: dict[str, object],
    applicable_checks: list[dict[str, object]],
    label: str,
) -> list[str]:
    problems: list[str] = []
    details = evidence.get("details")
    details = details if isinstance(details, dict) else {}
    attestation = details.get("attestation")
    if not isinstance(attestation, dict):
        return [f"{label}: lock-v4 G-IMPL PASS requires verified provider attestation metadata"]
    report_relative = attestation.get("report_path")
    report_path, report_error = safe_file(root, report_relative) if isinstance(report_relative, str) else (None, "report_path must be a repository-relative string")
    if report_error or report_path is None:
        return [f"{label}: attested CI report is unavailable: {report_error or 'file is missing'}"]
    if report_path.is_symlink():
        return [f"{label}: attested CI report cannot be a symbolic link"]
    actual_report_sha = file_sha256(report_path)
    if attestation.get("report_sha256") != actual_report_sha or evidence.get("record_sha256") != actual_report_sha:
        problems.append(f"{label}: attested CI report digest does not match current report bytes")
    report, report_error = load_json_object(report_path)
    if report_error or report is None:
        return problems + [f"{label}: attested CI report is invalid JSON: {report_error or 'invalid object'}"]

    repo = trusted_policy.get("repository")
    protected_ref = trusted_policy.get("protected_ref")
    expected_workflow = f"{repo}/.github/workflows/sdd-contract-validation.yml" if isinstance(repo, str) else ""
    gate_repo = record.get("repository")
    gate_repo_url = gate_repo.get("url_or_path") if isinstance(gate_repo, dict) else None
    parsed_gate_repo = urlparse(gate_repo_url) if isinstance(gate_repo_url, str) else None
    if (not isinstance(repo, str) or parsed_gate_repo is None or parsed_gate_repo.scheme != "https"
            or parsed_gate_repo.netloc != "github.com" or parsed_gate_repo.path.strip("/").lower() != repo
            or parsed_gate_repo.query or parsed_gate_repo.fragment or parsed_gate_repo.username or parsed_gate_repo.password):
        problems.append(f"{label}: trusted CI repository must match the gate record's GitHub repository")
    source_manifest_bytes, manifest_error = _git_blob(root, source_sha, APP_REQUIRED_CHECKS.as_posix())
    source_policy_bytes, policy_error = _git_blob(root, source_sha, APP_TRUSTED_CI.as_posix())
    if manifest_error:
        problems.append(f"{label}: {manifest_error}")
    if policy_error:
        problems.append(f"{label}: {policy_error}")
    if source_manifest_bytes is None or source_policy_bytes is None:
        return problems
    manifest_sha = "sha256:" + hashlib.sha256(source_manifest_bytes).hexdigest()
    if attestation.get("manifest_sha256") != manifest_sha:
        problems.append(f"{label}: attested required-check manifest digest does not match the gate source commit")
    try:
        source_manifest = json.loads(source_manifest_bytes)
        source_policy = json.loads(source_policy_bytes)
    except (UnicodeError, json.JSONDecodeError) as exc:
        return problems + [f"{label}: source-pinned CI policy or manifest is invalid JSON: {exc}"]
    if not isinstance(source_manifest, dict) or source_manifest.get("status") != "active":
        problems.append(f"{label}: source-pinned required-check manifest is not active")
    if not isinstance(source_policy, dict) or source_policy != trusted_policy:
        problems.append(f"{label}: trusted CI policy differs from the policy at the gate source commit")
    if isinstance(source_policy, dict) and (source_policy.get("repository") != repo or source_policy.get("protected_ref") != protected_ref or source_policy.get("status") != "active"):
        problems.append(f"{label}: source-pinned trusted CI policy is not active for the declared repository and protected ref")
    selected_task = record.get("gate_data", {}).get("selected_task_id") if isinstance(record.get("gate_data"), dict) else None
    pinned_checks = source_manifest.get("checks", []) if isinstance(source_manifest, dict) else []
    pinned_applicable = [
        item for item in pinned_checks
        if isinstance(item, dict) and item.get("required") is True
        and selected_task in item.get("task_ids", [])
    ] if isinstance(pinned_checks, list) else []
    if pinned_applicable != applicable_checks:
        problems.append(f"{label}: validator-required check set differs from the source-pinned manifest")

    provider_run = report.get("provider_run")
    if not isinstance(provider_run, dict):
        return problems + [f"{label}: attested report has no provider_run object"]
    expected_ref = protected_ref
    expected_workflow_ref = f"{expected_workflow}@{expected_ref}"
    expected_provider_fields = {
        "provider": "github-actions",
        "repository": repo,
        "event_name": "push",
        "ref": expected_ref,
        "ref_protected": True,
        "workflow_ref": expected_workflow_ref,
        "workflow_sha": source_sha,
        "tested_commit_sha": source_sha,
    }
    for field, expected in expected_provider_fields.items():
        if provider_run.get(field) != expected:
            problems.append(f"{label}: attested provider_run.{field} does not match trusted policy/source ({expected!r})")
    run_url = provider_run.get("run_url")
    if details.get("run_id_or_url") != run_url or not isinstance(run_url, str) or not re.fullmatch(
        rf"https://github\.com/{re.escape(str(repo))}/actions/runs/[0-9]+/attempts/[1-9][0-9]*", run_url
    ):
        problems.append(f"{label}: G-IMPL CI run URL does not match the attested provider run attempt")
    if report.get("manifest_status") != "active" or report.get("manifest_sha256") != manifest_sha:
        problems.append(f"{label}: attested report does not identify the active source-pinned required-check manifest")
    if report.get("overall_result") != "passed" or report.get("errors") != []:
        problems.append(f"{label}: attested required-check report is not an error-free pass")

    reported_checks = report.get("checks")
    checks_by_id = {item.get("check_id"): item for item in reported_checks if isinstance(item, dict)} if isinstance(reported_checks, list) else {}
    for expected in applicable_checks:
        check_id = expected.get("check_id")
        observed = checks_by_id.get(check_id)
        if expected.get("execution") != "ci":
            problems.append(f"{label}: required check '{check_id}' is manual; lock-v4 G-IMPL PASS requires CI-only checks")
            continue
        if not isinstance(observed, dict):
            problems.append(f"{label}: attested report omits required check '{check_id}'")
            continue
        expected_scope = ", ".join(sorted(expected.get("scope_paths", [])))
        for field, value in (
            ("result", "passed"),
            ("execution", "ci"),
            ("required", True),
            ("command_or_procedure", expected.get("command_or_procedure")),
            ("pass_condition", expected.get("pass_condition")),
            ("scope_paths", expected.get("scope_paths")),
            ("task_ids", expected.get("task_ids")),
            ("acceptance_criteria", expected.get("acceptance_criteria")),
            ("platforms", expected.get("platforms")),
        ):
            if observed.get(field) != value:
                problems.append(f"{label}: attested check '{check_id}' field '{field}' does not match the source manifest/required outcome")
        if observed.get("result") != "passed" or observed.get("exit_code") != 0:
            problems.append(f"{label}: attested required check '{check_id}' did not pass with exit code 0")
        if expected.get("scope_paths") and observed.get("scope") != expected_scope:
            problems.append(f"{label}: attested required check '{check_id}' scope differs from the source manifest")
    if len(applicable_checks) == 0:
        problems.append(f"{label}: no active required CI checks apply to the selected task")

    gh_path = shutil.which("gh")
    if gh_path is None:
        return problems + [f"{label}: GitHub CLI 'gh' is required to cryptographically verify G-IMPL attestation"]
    command = [
        gh_path, "attestation", "verify", str(report_path), "--repo", str(repo),
        "--signer-workflow", str(trusted_policy.get("signer_workflow")),
        "--signer-digest", str(trusted_policy.get("signer_digest")),
        "--source-digest", source_sha, "--source-ref", str(protected_ref),
        "--deny-self-hosted-runners", "--format", "json",
    ]
    try:
        verified = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return problems + [f"{label}: GitHub attestation verification unavailable: {exc}"]
    if verified.returncode != 0:
        diagnostic = (verified.stderr or verified.stdout).strip().replace("\n", " ")[:1000]
        return problems + [f"{label}: GitHub attestation verification failed: {diagnostic or 'gh returned a non-zero status'}"]
    try:
        verification_results = json.loads(verified.stdout)
    except json.JSONDecodeError as exc:
        return problems + [f"{label}: GitHub attestation verifier returned invalid JSON: {exc}"]
    expected_digest = actual_report_sha.removeprefix("sha256:")
    subject_match = False
    if isinstance(verification_results, list):
        for item in verification_results:
            result = item.get("verificationResult") if isinstance(item, dict) else None
            statement = result.get("statement") if isinstance(result, dict) else None
            subjects = statement.get("subject") if isinstance(statement, dict) else None
            if isinstance(subjects, list) and any(
                isinstance(subject, dict) and isinstance(subject.get("digest"), dict)
                and subject["digest"].get("sha256") == expected_digest
                for subject in subjects
            ):
                subject_match = True
                break
    if not subject_match:
        problems.append(f"{label}: verified provider attestation does not name the current report digest as its subject")
    return problems


def application_governance_problems(root: Path, gate_records: list[tuple[Path, dict[str, str]]]) -> list[str]:
    """Check a versioned app framework lock and gate handoff manifests when adopted."""
    lock_path = root / APP_FRAMEWORK_LOCK
    has_manifest = any((root / path).exists() for path in APP_HANDOFFS.values())
    gate_run_directory = root / APP_GATE_RUNS
    has_gate_runs = gate_run_directory.exists() or gate_run_directory.is_symlink()
    problems: list[str] = []
    # Pre-lock app repositories retain legacy gate-record semantics unless a
    # record explicitly claims versioned handoff evidence.
    declares_handoff = any("handoff-manifest" in data for _, data in gate_records)
    if not lock_path.exists() and not has_manifest and not declares_handoff and not has_gate_runs:
        return problems
    revision = ""
    if lock_path.exists():
        safe_lock_path, lock_path_error = safe_file(root, APP_FRAMEWORK_LOCK.as_posix())
        if lock_path_error or safe_lock_path is None:
            return [f"{APP_FRAMEWORK_LOCK.as_posix()}: {lock_path_error or 'could not resolve lock'}"]
        lock, parse_error = load_json_object(safe_lock_path)
        if parse_error or lock is None:
            return [f"{APP_FRAMEWORK_LOCK.as_posix()}: invalid JSON framework lock: {parse_error or 'invalid object'}"]
        lock_version = lock.get("lock_version")
        expected_fields_v1 = {"lock_version", "framework_repository", "framework_revision", "artifact_contract_id", "artifact_contract_version", "locked_files"}
        expected_fields_v2 = expected_fields_v1 | {"gate_contract_id", "gate_contract_version"}
        expected_fields = expected_fields_v1 if lock_version == 1 else expected_fields_v2
        if set(lock) != expected_fields:
            problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: fields must be exactly {', '.join(sorted(expected_fields))}")
        revision_value = lock.get("framework_revision")
        if lock_version not in APP_LOCK_VERSIONS or lock.get("artifact_contract_id") != "ARTIFACT-CONTRACT-001" or lock.get("artifact_contract_version") != 1:
            problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: unsupported framework or artifact contract version")
        if lock_version in {2, 3} and (lock.get("gate_contract_id") != "FRAMEWORK-GATE-CONTRACT-001" or lock.get("gate_contract_version") != "1.0"):
            problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: unsupported gate contract identity or version")
        if lock_version == 4 and (lock.get("gate_contract_id") != "FRAMEWORK-GATE-CONTRACT-001" or lock.get("gate_contract_version") != "1.2"):
            problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: lock version 4 requires FRAMEWORK-GATE-CONTRACT-001 v1.2")
        if not isinstance(revision_value, str) or not FRAMEWORK_REVISION_RE.fullmatch(revision_value):
            problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: framework_revision must be a 40-character lowercase commit SHA")
        else:
            revision = revision_value
        repository = lock.get("framework_repository")
        if not isinstance(repository, str) or not repository.startswith("https://github.com/"):
            problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: framework_repository must be an HTTPS GitHub repository URL")
        if lock_version == 4 and repository != CANONICAL_FRAMEWORK_URL:
            problems.append(
                f"{APP_FRAMEWORK_LOCK.as_posix()}: lock-v4 trusted CI requires the canonical framework repository "
                f"{CANONICAL_FRAMEWORK_URL}"
            )
        locked_files = lock.get("locked_files")
        expected_locked_files = (
            APP_LOCKED_FILES_V1 if lock_version == 1 else APP_LOCKED_FILES_V2 if lock_version == 2
            else APP_LOCKED_FILES_V3 if lock_version == 3 else APP_LOCKED_FILES_V4
        )
        if not isinstance(locked_files, dict) or set(locked_files) != set(expected_locked_files):
            problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: locked_files must cover exactly the files for framework lock version {lock_version}")
        else:
            for relative in expected_locked_files:
                expected_digest = locked_files.get(relative)
                path, error = safe_file(root, relative)
                if error or path is None:
                    problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()} ({relative}): locked file {error or 'is missing'}")
                elif not isinstance(expected_digest, str) or not SHA256_RE.fullmatch(expected_digest):
                    problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()} ({relative}): locked digest is malformed")
                elif file_sha256(path) != expected_digest:
                    problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()} ({relative}): file digest differs from the initialized framework snapshot")
        if lock_version in {3, 4}:
            _, manifest_problems = required_check_manifest(root)
            problems.extend(manifest_problems)
        if lock_version == 4:
            _, trusted_policy_problems = trusted_ci_policy(root)
            problems.extend(trusted_policy_problems)

    for gate_id, manifest_path in APP_HANDOFFS.items():
        if (root / manifest_path).exists():
            if not revision:
                problems.append(f"{manifest_path.as_posix()}: a versioned .sdd/framework.lock.json is required")
            else:
                problems.extend(validate_handoff_manifest(root, gate_id, revision))

    for path, data in gate_records:
        gate_id = data.get("gate-id", "")
        if gate_id not in APP_HANDOFFS:
            continue
        result = data.get("gate-result", "").lower()
        if not result:
            problems.append(f"{path.relative_to(root).as_posix()}: {gate_id} gate record must declare gate-result")
        elif result not in GATE_RESULTS:
            problems.append(f"{path.relative_to(root).as_posix()}: invalid gate-result '{data.get('gate-result')}'")
        if result in {"passed", "passed-with-accepted-risk"}:
            expected_manifest = APP_HANDOFFS[gate_id].as_posix()
            if data.get("handoff-manifest") != expected_manifest:
                problems.append(f"{path.relative_to(root).as_posix()}: passed {gate_id} record must link handoff-manifest '{expected_manifest}'")
            if not revision:
                problems.append(f"{path.relative_to(root).as_posix()}: passed {gate_id} record requires a versioned .sdd/framework.lock.json")
            if not (root / APP_HANDOFFS[gate_id]).is_file():
                problems.append(f"{path.relative_to(root).as_posix()}: passed {gate_id} record has no populated {expected_manifest}")

    if has_manifest and not lock_path.exists():
        problems.append(f"{APP_FRAMEWORK_LOCK.as_posix()}: required because a handoff manifest is present")
    if has_gate_runs and lock_path.exists():
        lock, _ = load_json_object(lock_path)
        if not lock or lock.get("lock_version") not in {2, 3, 4}:
            problems.append(f"{APP_GATE_RUNS.as_posix()}: version-2, version-3, or version-4 framework lock and explicit gate-contract migration are required")
        else:
            lock, _ = load_json_object(lock_path)
            contract_version = str(lock.get("gate_contract_version")) if lock else ""
            schema, schema_problems = _gate_schema_for_app(root, contract_version)
            problems.extend(schema_problems)
            if schema is not None:
                mission, mission_error = read_front_matter(root / "mission.md")
                mission_id = mission.get("id", "") if not mission_error else ""
                application_id = mission_id.removesuffix("-MISSION-001") if mission_id.endswith("-MISSION-001") else ""
                if not application_id:
                    problems.append("mission.md: application ID cannot be derived from canonical mission artifact identity")
                else:
                    problems.extend(validate_gate_run_records(root, schema, application_id))
    elif has_gate_runs:
        problems.append(f"{APP_GATE_RUNS.as_posix()}: version-2, version-3, or version-4 framework lock and explicit gate-contract migration are required")
    elif lock_path.exists():
        lock, _ = load_json_object(lock_path)
        if lock and lock.get("lock_version") in {2, 3, 4}:
            contract_version = str(lock.get("gate_contract_version"))
            schema, schema_problems = _gate_schema_for_app(root, contract_version)
            problems.extend(schema_problems)
    return problems


def safe_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    """Resolve a repository-relative file without allowing manifest path escape."""
    candidate_path = Path(relative)
    if candidate_path.is_absolute() or ".." in candidate_path.parts:
        return None, "path must be repository-relative and must not contain '..'"
    root_resolved = root.resolve()
    candidate = (root / candidate_path).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None, "path resolves outside the repository"
    if not candidate.is_file():
        return None, "required file is missing"
    return candidate, None


def section_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    """Find one exact Markdown heading and return its body bounds."""
    target = re.fullmatch(r"(#{1,6})\s+(.+?)\s*", heading)
    if not target:
        return None
    target_level = len(target.group(1))
    target_title = target.group(2).strip().rstrip("#").strip()
    matches = []
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line.strip())
        if match and len(match.group(1)) == target_level and match.group(2).strip() == target_title:
            matches.append(index)
    if len(matches) != 1:
        return None
    start = matches[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        match = re.match(r"^(#{1,6})\s+", lines[index].strip())
        if match and len(match.group(1)) <= target_level:
            end = index
            break
    return start, end


def split_table_row(line: str) -> list[str]:
    return [cell.strip().strip("`").strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def requirement_table_problems(
    root: Path,
    table_spec: dict[str, object],
    keywords: tuple[str, ...] = RFC_2119_KEYWORDS,
) -> list[str]:
    """Validate requirement tables in one explicitly configured document section."""
    relative = table_spec.get("path")
    heading = table_spec.get("heading")
    requirement_kind = table_spec.get("requirement_kind")
    minimum_rows = table_spec.get("minimum_rows")
    if not isinstance(relative, str) or not isinstance(heading, str):
        return ["requirement-table rule must define string path and heading fields"]
    if requirement_kind not in {"FR", "NFR"} or not isinstance(minimum_rows, int) or minimum_rows < 0:
        return [f"{relative}: requirement-table rule has invalid requirement_kind or minimum_rows"]
    path, error = safe_file(root, relative)
    if error or path is None:
        return [f"{relative}: {error or 'could not resolve file'}"]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"{relative}: could not read requirement document: {exc}"]
    bounds = section_bounds(lines, heading)
    if bounds is None:
        return [f"{relative}: required heading '{heading}' must occur exactly once"]
    start, end = bounds
    section_lines = lines[start:end]
    problem_prefix = f"{relative} ({heading})"
    table_runs: list[list[tuple[int, str]]] = []
    current_run: list[tuple[int, str]] = []
    for offset, line in enumerate(section_lines, start + 1):
        if line.strip().startswith("|") and line.strip().endswith("|"):
            current_run.append((offset, line))
        elif current_run:
            table_runs.append(current_run)
            current_run = []
    if current_run:
        table_runs.append(current_run)

    counted_rows = 0
    expected_headers = ("ID", "Requirement", "Acceptance evidence")
    keyword_pattern = re.compile(
        r"(?<![A-Za-z])(?:"
        + "|".join(re.escape(word) for word in sorted(keywords, key=len, reverse=True))
        + r")(?![A-Za-z])",
        re.IGNORECASE,
    )
    for table_number, run in enumerate(table_runs, 1):
        header_line, header_text = run[0]
        headers = tuple(split_table_row(header_text))
        if len(run) < 2 or not is_table_separator(run[1][1]):
            return [f"{problem_prefix}: table {table_number} at line {header_line} is missing a Markdown separator row"]
        if tuple(value.casefold() for value in headers) != tuple(value.casefold() for value in expected_headers):
            return [
                f"{problem_prefix}: table {table_number} at line {header_line} must use columns "
                "ID | Requirement | Acceptance evidence"
            ]
        for line_number, row_text in run[2:]:
            if is_table_separator(row_text):
                continue
            cells = split_table_row(row_text)
            if len(cells) != 3:
                return [f"{problem_prefix}: row at line {line_number} must contain exactly three columns"]
            artifact_id, statement, acceptance = cells
            if artifact_id.startswith("<") and artifact_id.endswith(">"):
                continue
            counted_rows += 1
            if not ID_RE.fullmatch(artifact_id):
                return [f"{problem_prefix}: row at line {line_number} has invalid stable ID '{artifact_id}'"]
            if requirement_kind not in artifact_id.split("-"):
                return [
                    f"{problem_prefix}: row at line {line_number} ID '{artifact_id}' must identify a {requirement_kind} requirement"
                ]
            if not statement:
                return [f"{problem_prefix}: row at line {line_number} has an empty Requirement cell"]
            if not acceptance:
                return [f"{problem_prefix}: row at line {line_number} has an empty Acceptance evidence cell"]
            matches = list(keyword_pattern.finditer(statement))
            uppercase_matches = [match.group(0) for match in matches if match.group(0) in keywords]
            if not uppercase_matches:
                return [
                    f"{problem_prefix}: row at line {line_number} must contain an uppercase RFC 2119 keyword "
                    "in the Requirement cell"
                ]
    if counted_rows < minimum_rows:
        return [
            f"{problem_prefix}: expected at least {minimum_rows} requirement row(s), found {counted_rows}"
        ]
    return []


def framework_contract_problems(root: Path) -> list[str]:
    """Load and enforce the framework repository's required-artifact contract."""
    contract_path, path_error = safe_file(root, FRAMEWORK_CONTRACT.as_posix())
    if path_error or contract_path is None:
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: required framework artifact contract is missing ({path_error})"]
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: invalid JSON artifact contract: {exc}"]
    if not isinstance(contract, dict) or contract.get("contract_id") != "ARTIFACT-CONTRACT-001" or contract.get("contract_version") != 1:
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: unsupported artifact contract identity or version"]
    profile = contract.get("framework")
    if not isinstance(profile, dict):
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: missing framework profile"]
    required_paths = profile.get("required_paths")
    required_artifacts = profile.get("required_artifacts")
    requirement_tables = profile.get("requirement_tables")
    keywords = contract.get("normative_keywords")
    if not isinstance(required_paths, list) or not all(isinstance(item, str) for item in required_paths):
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: framework required_paths must be a list of strings"]
    if not isinstance(required_artifacts, list) or not all(isinstance(item, dict) for item in required_artifacts):
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: framework required_artifacts must be a list of objects"]
    if not isinstance(requirement_tables, list) or not all(isinstance(item, dict) for item in requirement_tables):
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: framework requirement_tables must be a list of objects"]
    if (not isinstance(keywords, list) or not keywords or not all(isinstance(item, str) and item and item == item.upper() for item in keywords)
            or len(set(keywords)) != len(keywords)):
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: normative_keywords must be a non-empty list of unique uppercase strings"]
    keyword_tuple = tuple(keywords)
    if set(keyword_tuple) != set(RFC_2119_KEYWORDS):
        return [f"{FRAMEWORK_CONTRACT.as_posix()}: normative_keywords must match the supported RFC 2119 keyword set"]
    problems: list[str] = []
    for relative in required_paths:
        _, error = safe_file(root, relative)
        if error:
            problems.append(f"{relative}: required template file {error}")
    for artifact in required_artifacts:
        relative = artifact.get("path")
        expected_id = artifact.get("id")
        if not isinstance(relative, str) or not isinstance(expected_id, str):
            problems.append(f"{FRAMEWORK_CONTRACT.as_posix()}: each required artifact must define string path and id fields")
            continue
        path, error = safe_file(root, relative)
        if error or path is None:
            problems.append(f"{relative}: required artifact {error or 'could not resolve file'}")
            continue
        metadata, metadata_error = read_front_matter(path)
        if metadata_error:
            problems.append(f"{relative}: required artifact metadata could not be read: {metadata_error}")
        elif metadata.get("id") != expected_id:
            problems.append(
                f"{relative}: required artifact ID must be '{expected_id}', found '{metadata.get('id', '') or 'missing'}'"
            )
    for table_spec in requirement_tables:
        problems.extend(requirement_table_problems(root, table_spec, keyword_tuple))
    return problems


def application_requirement_problems(root: Path) -> list[str]:
    """Lint only configured requirement tables in an initialized app specification."""
    spec = root / "specification.md"
    if not spec.is_file():
        return []
    problems: list[str] = []
    for table_spec in APP_REQUIREMENT_TABLES:
        problems.extend(requirement_table_problems(root, table_spec))
    return problems


def command_list(_: argparse.Namespace) -> int:
    rows = []
    for path in markdown_files(ROOT):
        data, _ = read_front_matter(path)
        if data.get("id"):
            rows.append((data["id"], data.get("status", "?"), path.relative_to(ROOT).as_posix(), data.get("title", "")))
    for artifact_id, status, path, title in sorted(rows):
        print(f"{artifact_id:24} {status:20} {path} — {title}")
    print(f"{len(rows)} artifact(s)")
    missing = missing_app_canonical_files(ROOT)
    if missing:
        print(
            "ERROR incomplete app SDD layout; missing required root file(s): "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    return 0


def command_validate(_: argparse.Namespace) -> int:
    problems: list[str] = []
    seen: dict[str, Path] = {}
    gate_records: list[tuple[Path, dict[str, str]]] = []
    app_project = is_app_project(ROOT)
    if app_project:
        for filename in missing_app_canonical_files(ROOT):
            problems.append(f"{filename}: required app SDD root file is missing")
    elif not markdown_files(ROOT):
        problems.append("no artifacts discovered; refusing to validate an empty repository")
    if app_project:
        problems.extend(application_requirement_problems(ROOT))
    else:
        problems.extend(framework_contract_problems(ROOT))
    for path in markdown_files(ROOT):
        data, error = read_front_matter(path)
        rel = path.relative_to(ROOT).as_posix()
        if error:
            problems.append(f"{rel}: {error}")
            continue
        for key in REQUIRED:
            if not data.get(key):
                problems.append(f"{rel}: missing required field '{key}'")
        status = data.get("status", "")
        if status and status not in ALLOWED_STATUSES:
            problems.append(
                f"{rel}: invalid artifact status '{status}'; expected one of "
                f"{', '.join(sorted(ALLOWED_STATUSES))}"
            )
        gate_id = data.get("gate-id", "")
        declares_handoff_gate = gate_id in APP_HANDOFFS
        gate_record_type = data.get("type") in {"gate-record", "lifecycle-gate-record"}
        has_gate_metadata = any(key in data for key in ("gate-id", "gate-result", "handoff-manifest"))
        if has_gate_metadata and not gate_record_type:
            problems.append(
                f"{rel}: gate metadata requires type 'gate-record' or 'lifecycle-gate-record'"
            )
        if gate_record_type and gate_id not in GATE_IDS:
            problems.append(
                f"{rel}: gate record must declare a recognized gate-id; expected one of "
                f"{', '.join(sorted(GATE_IDS))}"
            )
        if "handoff-manifest" in data and gate_id not in APP_HANDOFFS:
            problems.append(f"{rel}: handoff-manifest is supported only for G-REQ or G-ARCH records")
        if gate_record_type or declares_handoff_gate:
            gate_records.append((path, data))
        artifact_id = data.get("id", "")
        if artifact_id:
            if not ID_RE.fullmatch(artifact_id):
                problems.append(f"{rel}: invalid artifact ID '{artifact_id}'")
            if artifact_id in seen:
                problems.append(f"{rel}: duplicate ID {artifact_id} (also {seen[artifact_id].relative_to(ROOT)})")
            else:
                seen[artifact_id] = path
            # Keep established human-readable workflow paths stable; their
            # metadata ID remains the canonical identity and is still checked
            # for presence and duplication. Other artifact paths are ID-led.
            canonical_app_file = app_project and path.parent == ROOT and path.name in APP_CANONICAL_FILES
            app_prefix = ""
            if app_project:
                mission, _ = read_front_matter(ROOT / "mission.md")
                app_prefix = mission.get("id", "").removesuffix("-MISSION-001")
            app_id_suffix = artifact_id.removeprefix(f"{app_prefix}-") if app_prefix else artifact_id
            stable_app_name = app_project and APP_STABLE_FILENAMES.get(data.get("type", "")) == path.name
            stable_workflow_path = not app_project and path.parent == ROOT / "workflows"
            valid_app_id_name = app_project and (
                path.stem == artifact_id or path.stem.startswith(artifact_id + "-")
                or path.stem == app_id_suffix or path.stem.startswith(app_id_suffix + "-")
                or stable_app_name
            )
            if not canonical_app_file and not stable_workflow_path and not valid_app_id_name and not path.name.startswith(artifact_id):
                problems.append(f"{rel}: filename must begin with {artifact_id}")
    if app_project:
        problems.extend(application_governance_problems(ROOT, gate_records))
    if problems:
        print("\n".join(f"ERROR {item}" for item in problems), file=sys.stderr)
        return 1
    print(f"Validated {len(seen)} artifact(s).")
    return 0


def command_new(args: argparse.Namespace) -> int:
    if not ID_RE.fullmatch(args.artifact_id):
        print("ID must look like ADR-001, PRD-014, or PRODUCT-ADV-001.", file=sys.stderr)
        return 2
    title = " ".join(args.title.split())
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "artifact"
    type_slug = re.sub(r"[^a-z0-9]+", "-", args.artifact_type.lower()).strip("-")
    app_project = is_app_project(ROOT)
    missing = missing_app_canonical_files(ROOT)
    if missing:
        print(
            "Refusing to create an artifact in an incomplete app SDD layout; "
            "missing required root file(s): " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2
    app_type_directories = {
        "decision": "decisions",
        "decision-record": "decisions",
        "review": "reviews",
        "adversarial-review": "reviews",
        "gate-record": "reviews",
        "architecture": "architecture",
        "adr": "architecture",
        "architecture-decision-record": "architecture",
        "feasibility-register": "architecture",
        "verification": "delivery/verification",
        "verification-record": "delivery/verification",
        "verification-plan": "delivery",
        "release": "delivery/releases",
        "release-record": "delivery/releases",
        "operations": "operations",
        "operations-runbook": "operations",
        "incident": "operations/incidents",
    }
    if app_project:
        directory = ROOT / app_type_directories.get(type_slug, f"docs/{type_slug}")
    else:
        directory = ROOT / "docs" / type_slug
    path = directory / f"{args.artifact_id}-{slug}.md"
    for existing in markdown_files(ROOT):
        data, _ = read_front_matter(existing)
        if data.get("id") == args.artifact_id:
            print(f"ID already exists in {existing.relative_to(ROOT)}", file=sys.stderr)
            return 2
    today = dt.date.today().isoformat()
    content = (
        "---\n"
        f"id: {args.artifact_id}\n"
        f"type: {type_slug}\n"
        f"title: {title}\n"
        "status: draft\n"
        "version: 0.1\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        "---\n\n"
        f"# {args.artifact_id} — {title}\n\n"
        "## Purpose\n\n"
        "<Why this artifact exists and what decision or work it supports.>\n\n"
        "## Content\n\n"
        "<Artifact-specific content.>\n\n"
        "## References\n\n- <Related artifact IDs and links>\n"
    )
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as artifact_file:
            artifact_file.write(content)
    except FileExistsError:
        print(f"Refusing to overwrite {path.relative_to(ROOT)}", file=sys.stderr)
        return 2
    print(path.relative_to(ROOT))
    return 0


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list discovered artifacts").set_defaults(run=command_list)
    sub.add_parser("validate", help="check front matter and artifact identities").set_defaults(run=command_validate)
    create = sub.add_parser("new", help="create a new Markdown artifact")
    create.add_argument("artifact_type", help="artifact type, used as the docs subdirectory")
    create.add_argument("artifact_id", help="stable ID, such as ADR-001")
    create.add_argument("title")
    create.set_defaults(run=command_new)
    return cli


if __name__ == "__main__":
    arguments = parser().parse_args()
    raise SystemExit(arguments.run(arguments))
