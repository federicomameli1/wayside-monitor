#!/usr/bin/env python3
"""Workflow wrapper around the Verdict SubjectRepoPipeline (Test Evidence).

Runs after `pytest --json-report` produced `test-report.json`. Reads that
report, the APCS doc bundle from `docs/`, and the current commit info,
then asks the LLM to decide whether the build is safe to promote.

Environment variables expected:
    OPENROUTER_API_KEY      (required for LLM synthesis; if missing the
                             pipeline falls back to a deterministic-only
                             verdict so the workflow never breaks)
    OPENROUTER_MODEL        (optional, forwarded to the client)
    COMMIT_SHA              (required) — full commit SHA being analyzed
    COMMIT_MESSAGE          (optional)
    COMMIT_AUTHOR           (optional)
    SUBJECT_REPO            (required) — e.g. owner/wayside-monitor
    TEST_REPORT_PATH        (optional, default: test-report.json)
    DOCS_DIR                (optional, default: docs)
    OUTPUT_DIR              (optional, default: test-evidence-output)
"""

from __future__ import annotations

import json
import os
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
    for path in sorted(docs_dir.glob("APCS_*.txt")):
        try:
            bundle[path.name] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return bundle


def _read_test_report(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _build_commit_info(sha: str) -> dict:
    diff_stat = ""
    changed_files: list = []
    try:
        diff_stat = subprocess.run(
            ["git", "show", "--stat", "--format=", sha],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        pass
    try:
        changed_files = subprocess.run(
            ["git", "show", "--name-only", "--format=", sha],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().splitlines()
    except subprocess.CalledProcessError:
        pass
    return {
        "commit_message": os.environ.get("COMMIT_MESSAGE", ""),
        "author": os.environ.get("COMMIT_AUTHOR", ""),
        "diff_stat": diff_stat,
        "changed_files": [f for f in changed_files if f],
    }


def _render_markdown(decision: dict, sha: str) -> str:
    verdict = str(decision.get("decision", "UNKNOWN")).upper()
    badge = {
        "GO": "✅ **GO**",
        "HOLD": "🟠 **HOLD**",
    }.get(verdict, f"❔ **{verdict}**")
    summary = decision.get("summary") or decision.get("reason") or "(no summary provided)"

    parts: list = [
        "## [Verdict] Test Evidence",
        "",
        f"**Verdict:** {badge}",
        "",
        f"**Summary:** {summary}",
        "",
    ]

    reasons = decision.get("reasons") or decision.get("findings") or []
    if isinstance(reasons, list) and reasons:
        parts.append("### Findings")
        parts.append("")
        for item in reasons:
            if isinstance(item, dict):
                title = item.get("title") or item.get("rule") or "Finding"
                detail = item.get("detail") or item.get("reason") or item.get("description") or ""
                parts.append(f"- **{title}**")
                if detail:
                    parts.append(f"  {detail}")
            else:
                parts.append(f"- {item}")
        parts.append("")

    parts.append(f"_Commit `{sha[:8]}` · automated test evidence review_")
    return "\n".join(parts)


def main() -> int:
    # Import after env validation so we get a clear error if the wrong dir
    # is in PYTHONPATH.
    from agents.llm_client import OpenRouterClient
    from agents.subject_pipeline import SubjectRepoPipeline
    from agents.test_report_parser import parse_pytest_json

    sha = _require_env("COMMIT_SHA")
    subject_repo = _require_env("SUBJECT_REPO")

    test_report_path = Path(os.environ.get("TEST_REPORT_PATH", "test-report.json"))
    docs_dir = Path(os.environ.get("DOCS_DIR", "docs"))
    output_dir = Path(os.environ.get("OUTPUT_DIR", "test-evidence-output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    test_summary = parse_pytest_json(_read_test_report(test_report_path))
    bundle = _read_docs_bundle(docs_dir)
    commit_info = _build_commit_info(sha)

    client = OpenRouterClient.from_env()
    if client is None:
        print("WARNING: OpenRouter client not configured; running deterministic-only.")

    pipeline = SubjectRepoPipeline(client=client)
    decision = pipeline.analyze(
        bundle=bundle,
        test_summary=test_summary,
        commit_info=commit_info,
        subject_repo=subject_repo,
        ref=sha,
    )

    markdown = _render_markdown(decision, sha)

    (output_dir / "report.md").write_text(markdown, encoding="utf-8")
    (output_dir / "result.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print(
        f"Test Evidence complete: decision={decision.get('decision')!r} "
        f"summary={(decision.get('summary') or '')[:80]!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
