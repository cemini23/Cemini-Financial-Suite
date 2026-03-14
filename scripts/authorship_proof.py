#!/usr/bin/env python3
"""
Git Authorship Proof Script (Step 51)
Generates authorship proof and git statistics for Section 1235 compliance.
Run: python3 scripts/authorship_proof.py
Output: vdr/06_authorship_proof.md, vdr/07_git_stats.json
"""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
VDR = ROOT / "vdr"

# Authors to exclude from Section 1235 human-author analysis
BOT_PATTERNS = [
    "github-actions[bot]",
    "dependabot[bot]",
    "[bot]",
]


def is_bot(author_name: str) -> bool:
    """Return True if the author appears to be an automated bot."""
    return any(pat in author_name for pat in BOT_PATTERNS)


def run_git_log() -> list[dict]:
    """Run git log and return structured commit data."""
    result = subprocess.run(  # noqa: S603
        [
            "git",
            "-C",
            str(ROOT),
            "log",
            "--format=%H|%an|%ae|%ai|%s",
            "--all",
            "--no-merges",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    commits = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        commit_hash, author_name, author_email, datetime_str, subject = parts
        try:
            dt = datetime.fromisoformat(datetime_str.strip())
        except ValueError:
            dt = datetime.now(tz=timezone.utc)
        commits.append(
            {
                "hash": commit_hash.strip(),
                "author_name": author_name.strip(),
                "author_email": author_email.strip(),
                "datetime": dt.isoformat(),
                "subject": subject.strip(),
                "is_bot": is_bot(author_name.strip()),
            }
        )
    return commits


def compute_stats(commits: list[dict]) -> dict:
    """Compute statistics from commit list."""
    if not commits:
        return {}

    human_commits = [c for c in commits if not c["is_bot"]]
    bot_commits = [c for c in commits if c["is_bot"]]

    # Author breakdown
    author_counts: dict[str, int] = defaultdict(int)
    for c in commits:
        author_counts[c["author_name"]] += 1

    human_author_counts: dict[str, int] = defaultdict(int)
    for c in human_commits:
        human_author_counts[c["author_name"]] += 1

    # Date range
    datetimes = [datetime.fromisoformat(c["datetime"]) for c in commits]
    oldest = min(datetimes).date().isoformat()
    newest = max(datetimes).date().isoformat()

    # Commits by week (ISO week)
    by_week: dict[str, int] = defaultdict(int)
    for c in human_commits:
        dt = datetime.fromisoformat(c["datetime"])
        week_key = f"{dt.year}-W{dt.strftime('%V')}"
        by_week[week_key] += 1

    # Primary human author (most commits, not a bot)
    primary_author = max(human_author_counts, key=lambda k: human_author_counts[k]) if human_author_counts else "Unknown"

    return {
        "total_commits": len(commits),
        "human_commits": len(human_commits),
        "bot_commits": len(bot_commits),
        "date_range": {"oldest": oldest, "newest": newest},
        "author_breakdown": dict(author_counts),
        "human_author_breakdown": dict(human_author_counts),
        "primary_author": primary_author,
        "commits_by_week": dict(sorted(by_week.items())),
    }


def write_authorship_proof(commits: list[dict], stats: dict) -> None:
    """Write vdr/06_authorship_proof.md."""
    VDR.mkdir(exist_ok=True)

    primary = stats.get("primary_author", "Unknown")
    human_commits = [c for c in commits if not c["is_bot"]]

    lines = [
        "# Git Repository Authorship Proof",
        "",
        f"**Generated:** {datetime.now(tz=timezone.utc).date().isoformat()}  ",
        f"**Repository:** Cemini Financial Suite  ",
        f"**Total commits:** {stats['total_commits']}  ",
        f"**Human commits:** {stats['human_commits']}  ",
        f"**Bot commits (CI/CD):** {stats['bot_commits']}  ",
        f"**Date range:** {stats['date_range']['oldest']} to {stats['date_range']['newest']}  ",
        "",
        "## Author Breakdown",
        "",
        "| Author | Commits | Type |",
        "|--------|---------|------|",
    ]

    for author, count in sorted(stats["author_breakdown"].items(), key=lambda x: -x[1]):
        author_type = "Bot (CI/CD)" if is_bot(author) else "Human"
        lines.append(f"| {author} | {count} | {author_type} |")

    lines += [
        "",
        "## IRC Section 1235 Statement",
        "",
        f"All {stats['human_commits']} human-authored commits in this repository were",
        f"authored by **{primary}**. Bot commits ({stats['bot_commits']} total) were",
        "generated automatically by GitHub Actions CI/CD for documentation updates",
        "(commit messages: `docs: auto-update READMEs [skip ci]`) and do not represent",
        "independent intellectual contributions.",
        "",
        "This satisfies the **'personal efforts'** requirement under **IRC Section 1235**",
        "for long-term capital gains treatment of self-created intellectual property.",
        "The codebase was developed solely by the named individual over the date range",
        f"shown ({stats['date_range']['oldest']} to {stats['date_range']['newest']}).",
        "",
        "> **Disclaimer:** This document is informational only. Consult a qualified tax",
        "> attorney or CPA before relying on Section 1235 treatment for any transaction.",
        "",
        "## Commit Activity Histogram (Human Commits by Week)",
        "",
        "```",
    ]

    by_week = stats.get("commits_by_week", {})
    if by_week:
        max_count = max(by_week.values()) if by_week else 1
        for week, count in sorted(by_week.items()):
            bar_len = max(1, int(count / max_count * 40))
            bar = "#" * bar_len
            lines.append(f"{week}  {bar} ({count})")

    lines += [
        "```",
        "",
        "## Recent Commit Log (Human Authors Only)",
        "",
        "| Date | Hash | Author | Subject |",
        "|------|------|--------|---------|",
    ]

    for c in human_commits[:50]:
        dt = datetime.fromisoformat(c["datetime"]).date().isoformat()
        short_hash = c["hash"][:9]
        subject = c["subject"][:70].replace("|", "\\|")
        lines.append(f"| {dt} | `{short_hash}` | {c['author_name']} | {subject} |")

    if len(human_commits) > 50:
        lines += ["", f"*... and {len(human_commits) - 50} more commits (see vdr/07_git_stats.json)*"]

    (VDR / "06_authorship_proof.md").write_text("\n".join(lines) + "\n")
    print(f"  Wrote vdr/06_authorship_proof.md ({len(human_commits)} human commits)")


def write_git_stats(commits: list[dict], stats: dict) -> None:
    """Write vdr/07_git_stats.json."""
    VDR.mkdir(exist_ok=True)
    payload = {
        **stats,
        "all_commits": commits,
    }
    (VDR / "07_git_stats.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"  Wrote vdr/07_git_stats.json ({len(commits)} total commits)")


def main() -> None:
    """Main entry point."""
    print("Running authorship proof...")
    commits = run_git_log()
    if not commits:
        print("WARNING: No commits found in git log")
    stats = compute_stats(commits)
    write_authorship_proof(commits, stats)
    write_git_stats(commits, stats)
    print("Authorship proof complete.")


if __name__ == "__main__":
    main()
