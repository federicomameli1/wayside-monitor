#!/usr/bin/env python3
"""Workflow wrapper around the Verdict pr_review module.

Runs on the GitHub Actions runner during pull-request workflows.
Reads the PR diff, runs the LLM-based review, writes the markdown
report and structured JSON to disk for upload as artifacts and
posting as a PR comment.

Environment variables expected:
    OPENROUTER_API_KEY      (required) — Verdict's LLM client
    HUGGINGFACE_TOKEN       (required) — Verdict's RAG embeddings
    PR_NUMBER, PR_TITLE, PR_AUTHOR, PR_BRANCH, PR_HEAD_SHA
                            (required) — passed by the workflow from PR event
    DOCS_DIR                (optional, default: docs)
    OUTPUT_DIR              (optional, default: pr-review-output)
    HF_EMBEDDING_MODEL      (optional) — forwarded to the embeddings client
    OPENROUTER_MODEL        (optional) — forwarded to the LLM client
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"ERROR: missing required env var {name}")
    return value


def _fetch_open_tickets(repo: str, token: str) -> list:
    """Fetch open GitHub Issues for the subject repo (PRs excluded)."""
    url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=50"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            items = json.loads(resp.read())
    except Exception as exc:
        print(f"WARNING: could not fetch open tickets: {exc}", file=sys.stderr)
        return []
    return [i for i in items if "pull_request" not in i]


def main() -> int:
    # The verdict repo is cloned by the workflow into VERDICT_PATH and
    # added to PYTHONPATH so we can import the pr_review module.
    from agents.pr_review import PRReviewError, PRReviewInput, PRReviewRunner
    from agents.pr_review.models import OpenTicket, PRMeta

    pr_number = int(_require_env("PR_NUMBER"))
    pr_meta = PRMeta(
        number=pr_number,
        title=os.environ.get("PR_TITLE", ""),
        author=os.environ.get("PR_AUTHOR", ""),
        branch=os.environ.get("PR_BRANCH", ""),
        base=os.environ.get("PR_BASE", "main"),
        head_sha=os.environ.get("PR_HEAD_SHA", ""),
    )

    docs_dir = os.environ.get("DOCS_DIR", "docs")
    output_dir = Path(os.environ.get("OUTPUT_DIR", "pr-review-output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    diff = subprocess.run(
        ["git", "diff", f"origin/{pr_meta.base}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    if not diff.strip():
        print("Empty diff — skipping review.")
        (output_dir / "report.md").write_text(
            "## [Verdict] LLM Review\n\n_Empty diff against base branch — nothing to review._\n",
            encoding="utf-8",
        )
        (output_dir / "result.json").write_text(
            json.dumps({"verdict": "GO", "summary": "Empty diff", "highlights": []}, indent=2),
            encoding="utf-8",
        )
        return 0

    runner = PRReviewRunner.from_env()
    if runner is None:
        sys.exit(
            "ERROR: PRReviewRunner.from_env() returned None — "
            "check OPENROUTER_API_KEY and HUGGINGFACE_TOKEN are set."
        )

    github_token = os.environ.get("GITHUB_TOKEN", "")
    subject_repo = os.environ.get("GITHUB_REPOSITORY", "")
    raw_tickets = _fetch_open_tickets(subject_repo, github_token) if github_token and subject_repo else []
    open_tickets = [
        OpenTicket(
            number=t["number"],
            title=t.get("title", ""),
            body=(t.get("body") or "")[:300] or None,
            labels=[lbl["name"] for lbl in (t.get("labels") or [])],
        )
        for t in raw_tickets
    ]
    if open_tickets:
        print(f"Fetched {len(open_tickets)} open ticket(s) as context.")

    review_input = PRReviewInput(
        diff_unified=diff,
        docs_dir=docs_dir,
        pr_meta=pr_meta,
        open_tickets=open_tickets,
    )

    try:
        output = runner.run(review_input)
    except PRReviewError as exc:
        sys.exit(f"ERROR: pr_review failed: {exc}")

    (output_dir / "report.md").write_text(output.report_markdown, encoding="utf-8")
    (output_dir / "result.json").write_text(
        output.model_dump_json(indent=2), encoding="utf-8"
    )
    print(f"PR review complete: verdict={output.verdict.value}, highlights={len(output.highlights)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
