#!/usr/bin/env python3
"""Workflow wrapper around the Verdict VDD Drafter.

Runs on the wayside-monitor deploy-prod workflow after a release is
published. Collects the available evidence (release metadata, cumulative
diff from the previous tag, APCS docs bundle, module versions) and asks
the LLM to draft the full VDD.

Environment variables expected:
    OPENROUTER_API_KEY      (required)
    OPENROUTER_MODEL        (optional)
    RELEASE_TAG             (required) e.g. v0.1.0
    RELEASE_NAME            (optional)
    RELEASE_BODY            (optional)
    RELEASE_URL             (optional)
    HEAD_SHA                (required)
    PREVIOUS_TAG            (optional; if unset the script tries to
                             auto-detect via 'git describe --tags --abbrev=0 HEAD^')
    SUBJECT_REPO            (required) e.g. owner/wayside-monitor
    IMAGE_REPOSITORY        (optional)
    DOCS_DIR                (optional, default: docs)
    OUTPUT_DIR              (optional, default: vdd-output)
    OUTPUT_FILE             (optional, default: VDDs/VDD-${RELEASE_TAG}.md)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"ERROR: missing required env var {name}")
    return value


def _read_docs_bundle(docs_dir: Path) -> dict:
    if not docs_dir.is_dir():
        return {}
    bundle: dict = {}
    for path in sorted(docs_dir.glob("*.txt")):
        try:
            bundle[path.name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return bundle


_VERSION_RE = re.compile(r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]')


def _discover_module_versions(repo_root: Path):
    from agents.vdd_drafter.models import ModuleVersion

    results = []
    for init_path in sorted(repo_root.glob("*/__init__.py")):
        if init_path.parent.name.startswith(".") or init_path.parent.name in {
            "tests",
            "test",
            "deploy",
            "config",
        }:
            continue
        try:
            text = init_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = _VERSION_RE.search(text)
        if not match:
            continue
        results.append(
            ModuleVersion(
                name=init_path.parent.name,
                version=match.group(1),
                source_path=str(init_path.relative_to(repo_root)),
            )
        )
    return results


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return ""


def _resolve_previous_tag(head_sha: str) -> str:
    explicit = os.environ.get("PREVIOUS_TAG", "").strip()
    if explicit:
        return explicit
    # Find the tag just before this commit.
    out = _git("describe", "--tags", "--abbrev=0", f"{head_sha}^").strip()
    return out


def main() -> int:
    from agents.vdd_drafter import VDDDraftInput, VDDDrafterError, VDDDrafterRunner

    release_tag = _require_env("RELEASE_TAG")
    head_sha = _require_env("HEAD_SHA")
    subject_repo = _require_env("SUBJECT_REPO")

    docs_dir = Path(os.environ.get("DOCS_DIR", "docs"))
    output_dir = Path(os.environ.get("OUTPUT_DIR", "vdd-output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_output_file = Path(
        os.environ.get("OUTPUT_FILE", f"VDDs/VDD-{release_tag}.md")
    )

    previous_tag = _resolve_previous_tag(head_sha)
    if previous_tag:
        diff_range = f"{previous_tag}..{head_sha}"
        diff_unified = _git("diff", diff_range)
        diff_stat = _git("diff", "--stat", diff_range)
    else:
        # First release or detached tag — fall back to a single-commit diff.
        diff_unified = _git("show", "--no-color", head_sha)
        diff_stat = _git("show", "--stat", "--format=", head_sha)

    docs_bundle = _read_docs_bundle(docs_dir)
    module_versions = _discover_module_versions(Path.cwd())

    runner = VDDDrafterRunner.from_env()
    if runner is None:
        sys.exit("ERROR: VDD drafter not configured (OPENROUTER_API_KEY missing)")

    draft_input = VDDDraftInput(
        release_tag=release_tag,
        release_name=os.environ.get("RELEASE_NAME", ""),
        release_body=os.environ.get("RELEASE_BODY", ""),
        release_url=os.environ.get("RELEASE_URL") or None,
        repo=subject_repo,
        previous_tag=previous_tag or None,
        head_sha=head_sha,
        diff_unified=diff_unified,
        diff_stat=diff_stat,
        docs_bundle=docs_bundle,
        module_versions=module_versions,
        image_repository=os.environ.get("IMAGE_REPOSITORY") or None,
    )

    try:
        output = runner.run(draft_input)
    except VDDDrafterError as exc:
        sys.exit(f"ERROR: VDD drafter failed: {exc}")

    # Persist locally for the artifact upload + the workflow's commit step.
    (output_dir / "VDD.md").write_text(output.vdd_markdown, encoding="utf-8")
    repo_output_file.parent.mkdir(parents=True, exist_ok=True)
    repo_output_file.write_text(output.vdd_markdown, encoding="utf-8")

    print(
        f"VDD drafted: {repo_output_file} "
        f"(sections present: {len(output.sections_present)}, "
        f"missing: {len(output.sections_missing)})"
    )
    if output.sections_missing:
        print(f"  Missing sections: {', '.join(output.sections_missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
