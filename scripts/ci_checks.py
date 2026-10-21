#!/usr/bin/env python3
"""Run app-declared required checks and write revision-bound CI evidence."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from artifacts import required_check_manifest

ROOT = Path(os.environ.get("SDD_REPOSITORY_ROOT", Path(__file__).resolve().parents[1])).resolve()
MANIFEST = ROOT / ".sdd/required-checks.json"
MAX_COMMAND_SECONDS = 600
SECRET_NAME = re.compile(r"(?:TOKEN|SECRET|PASSWORD|PRIVATE.?KEY|CREDENTIAL)", re.IGNORECASE)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def command_env() -> dict[str, str]:
    """Pass runner basics and CI identity, excluding variables that look secret."""
    allowed_prefixes = ("GITHUB_", "RUNNER_", "CI", "LANG", "LC_")
    allowed_exact = {"PATH", "HOME", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "PATHEXT", "SHELL"}
    return {
        key: value
        for key, value in os.environ.items()
        if (key in allowed_exact or key.startswith(allowed_prefixes)) and not SECRET_NAME.search(key)
    }


def run_command(command: str, cwd: Path, env: dict[str, str]) -> tuple[int | None, str, str, str | None]:
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            ["bash", "--noprofile", "--norc", "-euo", "pipefail", "-c", command],
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=(os.name == "posix"),
        )
        stdout, stderr = process.communicate(timeout=MAX_COMMAND_SECONDS)
        return process.returncode, stdout, stderr, None
    except subprocess.TimeoutExpired:
        if process is None:
            return None, "", "", f"command timed out after {MAX_COMMAND_SECONDS} seconds"
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr, f"command timed out after {MAX_COMMAND_SECONDS} seconds; process group was terminated"
    except OSError as exc:
        return None, "", "", f"could not execute command: {exc}"


def repository_sha() -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True)
        sha = result.stdout.strip().lower()
        if re.fullmatch(r"[a-f0-9]{40}", sha):
            return sha, None
        return None, "git rev-parse returned an invalid commit SHA"
    except (OSError, subprocess.CalledProcessError) as exc:
        return None, f"could not identify checked-out Git revision: {exc}"


def clean_checkout_problem(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"could not verify checkout cleanliness: {exc}"
    if result.stdout.strip():
        return "required checks must start from and preserve a clean checkout"
    return None


def github_metadata(sha: str | None) -> dict[str, object]:
    env = os.environ
    provider = "github-actions" if env.get("GITHUB_ACTIONS") == "true" else "local"
    repository = env.get("GITHUB_REPOSITORY")
    run_id = env.get("GITHUB_RUN_ID")
    attempt = env.get("GITHUB_RUN_ATTEMPT")
    run_url = f"https://github.com/{repository}/actions/runs/{run_id}/attempts/{attempt}" if repository and run_id and attempt else None
    event_head_sha = None
    event_base_sha = None
    event_path = env.get("GITHUB_EVENT_PATH")
    if event_path:
        try:
            event = json.loads(Path(event_path).read_text(encoding="utf-8"))
            pull = event.get("pull_request", {}) if isinstance(event, dict) else {}
            head = pull.get("head", {}) if isinstance(pull, dict) else {}
            base = pull.get("base", {}) if isinstance(pull, dict) else {}
            event_head_sha = head.get("sha") if isinstance(head, dict) else None
            event_base_sha = base.get("sha") if isinstance(base, dict) else None
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
    return {
        "provider": provider,
        "repository": repository,
        "workflow": env.get("GITHUB_WORKFLOW"),
        "workflow_ref": env.get("GITHUB_WORKFLOW_REF"),
        "workflow_sha": env.get("GITHUB_WORKFLOW_SHA"),
        "job": env.get("GITHUB_JOB"),
        "run_id": run_id,
        "run_attempt": int(attempt) if attempt and attempt.isdigit() else None,
        "run_url": run_url,
        "event_name": env.get("GITHUB_EVENT_NAME", "local"),
        "ref": env.get("GITHUB_REF", "local"),
        "ref_protected": env.get("GITHUB_REF_PROTECTED", "false").lower() == "true",
        "event_head_sha": event_head_sha,
        "event_base_sha": event_base_sha,
        "tested_commit_sha": sha,
        "runner_os": env.get("RUNNER_OS", "local"),
        "runner_arch": env.get("RUNNER_ARCH", "local"),
        "runner_image_os": env.get("ImageOS"),
        "runner_image_version": env.get("ImageVersion"),
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def main() -> int:
    configured_output = os.environ.get("SDD_CI_EVIDENCE_DIR")
    output_dir = Path(configured_output) if configured_output else Path(tempfile.mkdtemp(prefix="sdd-ci-evidence-"))
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir = output_dir.resolve()
    if output_dir == ROOT or ROOT in output_dir.parents:
        print("SDD_CI_EVIDENCE_DIR must be outside the checked-out repository", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "required-check-results.json"
    report: dict[str, object] = {"manifest_version": 1, "checks": [], "overall_result": "failed"}
    errors: list[str] = []
    manifest_valid = True
    try:
        manifest, manifest_problems = required_check_manifest(ROOT)
        if manifest is None or manifest_problems:
            manifest_valid = False
            errors.extend(manifest_problems or ["required-check manifest is invalid"])
            manifest = {"status": "invalid", "checks": []}
        report["manifest_sha256"] = digest(MANIFEST)
        report["manifest_status"] = manifest.get("status")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"invalid required-check manifest: {exc}")
        manifest = {"status": "invalid", "checks": []}

    checked_sha, sha_error = repository_sha()
    if sha_error:
        errors.append(sha_error)
    expected_sha = os.environ.get("GITHUB_SHA", "").lower()
    if expected_sha and checked_sha != expected_sha:
        errors.append(f"checked-out SHA {checked_sha!r} does not match provider event SHA {expected_sha!r}")
    provider = github_metadata(checked_sha)
    report["provider_run"] = provider
    report["manifest_path"] = ".sdd/required-checks.json"
    report["errors"] = errors
    check_results: list[dict[str, object]] = []
    env = command_env()
    checks = manifest.get("checks", []) if manifest_valid and isinstance(manifest, dict) else []
    tree_problem = clean_checkout_problem(ROOT)
    if tree_problem:
        errors.append(tree_problem)
        checks = []
    for check in checks:
        if not isinstance(check, dict):
            errors.append("manifest contains a non-object check entry")
            continue
        check_id = str(check.get("check_id", "unknown"))
        required = check.get("required") is True
        execution = check.get("execution")
        entry: dict[str, object] = {
            "check_id": check_id,
            "required": required,
            "execution": execution,
            "task_ids": check.get("task_ids"),
            "acceptance_criteria": check.get("acceptance_criteria"),
            "platforms": check.get("platforms"),
            "scope_paths": check.get("scope_paths"),
            "command_or_procedure": check.get("command_or_procedure"),
            "pass_condition": check.get("pass_condition"),
            "evidence_location": check.get("evidence_location"),
        }
        if not required:
            entry["result"] = "not-required"
        elif execution == "manual":
            entry["result"] = "manual-required"
        elif execution != "ci":
            entry["result"] = "invalid-execution-mode"
            errors.append(f"{check_id}: unsupported execution mode")
        else:
            runtime_version = None
            runtime_command = check.get("runtime_probe")
            if isinstance(runtime_command, str) and runtime_command.strip():
                runtime_exit, runtime_out, runtime_err, runtime_error = run_command(runtime_command, ROOT, env)
                runtime_version = runtime_out.strip()[:1000]
                entry["runtime_probe"] = runtime_command
                entry["runtime_probe_exit_code"] = runtime_exit
                if runtime_error or runtime_exit != 0:
                    entry["runtime_probe_stderr"] = runtime_err[-4000:]
                    entry["result"] = "failed"
                    errors.append(f"{check_id}: runtime probe failed: {runtime_error or runtime_exit}")
                tree_problem = clean_checkout_problem(ROOT)
                if tree_problem:
                    entry["result"] = "failed"
                    errors.append(f"{check_id}: {tree_problem}; command was not run")
            entry["observed_runtime"] = runtime_version
            command = check.get("command_or_procedure")
            if entry.get("result") != "failed" and isinstance(command, str):
                exit_code, stdout, stderr, run_error = run_command(command, ROOT, env)
                safe_id = re.sub(r"[^A-Za-z0-9._-]", "_", check_id)
                stdout_path = output_dir / f"{safe_id}.stdout.txt"
                stderr_path = output_dir / f"{safe_id}.stderr.txt"
                stdout_path.write_text(stdout, encoding="utf-8")
                stderr_path.write_text(stderr, encoding="utf-8")
                entry.update({
                    "exit_code": exit_code,
                    "stdout_path": stdout_path.relative_to(ROOT).as_posix() if stdout_path.is_relative_to(ROOT) else str(stdout_path),
                    "stdout_sha256": digest(stdout_path),
                    "stderr_path": stderr_path.relative_to(ROOT).as_posix() if stderr_path.is_relative_to(ROOT) else str(stderr_path),
                    "stderr_sha256": digest(stderr_path),
                    "result": "passed" if exit_code == 0 and run_error is None else "failed",
                })
                if run_error:
                    entry["error"] = run_error
                if exit_code != 0 or run_error:
                    errors.append(f"{check_id}: command failed: {run_error or exit_code}")
                tree_problem = clean_checkout_problem(ROOT)
                if tree_problem:
                    errors.append(f"{check_id}: {tree_problem}; remaining checks were not run")
                    check_results.append(entry)
                    break
        check_results.append(entry)

    if not errors:
        report["overall_result"] = "passed"
    report["checks"] = check_results
    report["errors"] = errors
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Required-check evidence: {report_path}")
    print(f"Check result: {report['overall_result']}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
