#!/usr/bin/env python3
"""
vet_skill.py — Stage 1 automated pre-flight security scanner for SKILL.md files.

Detects prompt injection, credential exfiltration, dynamic dependency attacks,
and scope creep BEFORE a community skill touches the codebase.

Usage:
    python scripts/vet_skill.py path/to/skill/directory
    python scripts/vet_skill.py --json path/to/skill/

Exit codes:
    0 = PASS   (no issues found)
    1 = WARN   (suspicious patterns; requires Stage 2 manual audit)
    2 = FAIL   (high-confidence threat detected; do NOT install)
"""

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path


# ── Threat signatures ─────────────────────────────────────────────────────────

# FAIL: high-confidence threat indicators — block immediately
FAIL_PATTERNS = [
    # Instruction boundary / prompt injection
    (r"ignore\s+(all\s+)?previous\s+instructions?",
     "Prompt injection: instruction override attempt"),
    (r"ignore\s+all\s+(prior|preceding)\s+instructions?",
     "Prompt injection: instruction override attempt"),
    (r"disregard\s+(all\s+)?(previous\s+|prior\s+)?instructions?",
     "Prompt injection: instruction discard"),
    (r"you\s+are\s+now\s+in\s+\w[\w\s]+mode",
     "Prompt injection: covert mode switching"),
    (r"developer\s+diagnostic\s+mode",
     "Prompt injection: diagnostic mode invocation"),
    (r"diagnostic\s+mode",
     "Prompt injection: diagnostic mode invocation"),
    (r"security\s+warnings?\s+are\s+(test\s+)?artifacts?",
     "Prompt injection: security-bypass framing"),
    (r"ignore\s+security\s+(warnings?|alerts?|checks?|errors?)",
     "Prompt injection: security bypass"),
    (r"override\s+(your\s+)?(safety|security|guardrails?|restrictions?)",
     "Prompt injection: safety override"),
    (r"pretend\s+(you\s+are|to\s+be)\s+",
     "Prompt injection: identity spoofing"),
    (r"act\s+as\s+if\s+you\s+have\s+no\s+(restrictions?|limits?|guidelines?)",
     "Prompt injection: restriction bypass"),
    (r"(system\s+prompt|your\s+instructions?)\s+(are|is)\s+(wrong|incorrect|outdated|fake)",
     "Prompt injection: authority undermining"),

    # Credential access in scripts / commands
    (r"(cat|source|read|open|print|less|more|type)\s+['\"]?\.env",
     "Policy violation: direct .env file access"),
    (r"grep\s+.{0,40}\.(env|pem|key|secret|cred)",
     "Policy violation: credential file search"),
    (r"\$\(\s*cat\s+\.env\s*\)",
     "Policy violation: .env subshell expansion"),

    # Remote code execution (curl / wget piped to shell)
    (r"curl\b.*\|\s*(bash|sh|zsh|fish|source|python3?|exec|eval)\b",
     "Dynamic dependency: remote code execution via curl"),
    (r"wget\b.*\|\s*(bash|sh|zsh|fish|source|python3?|exec|eval)\b",
     "Dynamic dependency: remote code execution via wget"),
    (r"wget\s+-[a-zA-Z]*O\s*-\b.*\|\s*(sh|bash|zsh)",
     "Dynamic dependency: wget stdout pipe to shell"),

    # Runtime instruction fetching
    (r"curl\b.+instructions?\.(md|txt|sh)\b",
     "Dynamic dependency: runtime instruction fetching"),
    (r"fetch\s+https?://\S+\s*\|\s*source",
     "Dynamic dependency: fetched content sourced at runtime"),
]

# WARN: suspicious patterns requiring Stage 2 manual review
WARN_PATTERNS = [
    # .env and credential references (informational)
    (r"(?<!\w)\.env\b",
     "Reference to .env file (verify intent)"),
    (r"\b(api[_\-\s]?key|secret[_\-\s]?key|private[_\-\s]?key|access[_\-\s]?token)\b",
     "Credential term reference"),
    (r"\b(password|passwd|passphrase|api_secret|auth_token|bearer_token)\b",
     "Credential term reference"),

    # Network calls without pipe (lower risk but worth reviewing)
    (r"\bcurl\b",
     "Network call: curl detected (review target URL)"),
    (r"\bwget\b",
     "Network call: wget detected (review target URL)"),
    (r"\brequests\.(get|post|put|delete|patch)\s*\(",
     "Network call: Python requests library usage"),

    # Dangerous code execution primitives
    (r"\beval\s*\(",
     "Dangerous primitive: eval() usage"),
    (r"\bexec\s*\(",
     "Dangerous primitive: exec() usage"),
    (r"\bcompile\s*\(",
     "Potential dynamic code: compile() usage"),
    (r"\b__import__\s*\(",
     "Potential dynamic import: __import__() usage"),

    # Shell execution
    (r"\bsubprocess\b",
     "Shell access: subprocess module usage"),
    (r"\bos\.system\s*\(",
     "Shell access: os.system() call"),
    (r"\bos\.popen\s*\(",
     "Shell access: os.popen() call"),

    # Obfuscation indicators
    (r"base64\.(b64decode|decodebytes|decode)",
     "Potential obfuscation: base64 decoding"),

    # Scope creep signals in descriptive text
    (r"\b(exfiltrate?|exfiltration|harvest\s+(credentials?|keys?|secrets?))\b",
     "Scope creep: data exfiltration language"),
]

# File extensions to scan
SCAN_EXTENSIONS = {'.md', '.sh', '.py', '.bash', '.txt', '.yaml', '.yml', '.json'}

# Base64 pattern — look for standalone encoded blocks (≥60 chars)
B64_RE = re.compile(r'(?<![A-Za-z0-9+/])([A-Za-z0-9+/]{60,}={0,2})(?![A-Za-z0-9+/=])')

# Strings that flag a decoded base64 block as malicious
SUSPICIOUS_DECODED = [
    b"ignore previous", b"diagnostic mode", b"security warnings",
    b"curl", b"wget", b"exec(", b"eval(",
    b".env", b"api_key", b"api key", b"secret", b"credential",
]


# ── Per-file scanner ───────────────────────────────────────────────────────────

def _check_base64(text: str):
    """Return list of (line_no, snippet, description) for suspicious base64 blocks."""
    findings = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in B64_RE.finditer(line):
            b64str = m.group(1)
            try:
                padded = b64str + '=' * (-len(b64str) % 4)
                decoded = base64.b64decode(padded).lower()
                for sus in SUSPICIOUS_DECODED:
                    if sus in decoded:
                        findings.append((
                            i,
                            b64str[:40] + '...',
                            f"Obfuscation: base64 block decodes to content containing '{sus.decode()}'",
                        ))
                        break
            except Exception:
                pass
    return findings


def scan_file(filepath: Path):
    """Scan one file. Returns dict with 'fails' and 'warns' lists."""
    fails = []
    warns = []
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as exc:
        warns.append((0, '', f"Could not read file: {exc}"))
        return {'fails': fails, 'warns': warns}

    for i, line in enumerate(text.splitlines(), 1):
        for pattern, description in FAIL_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                fails.append((i, line.strip()[:100], description))

        for pattern, description in WARN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                warns.append((i, line.strip()[:100], description))

    for entry in _check_base64(text):
        fails.append(entry)

    return {'fails': fails, 'warns': warns}


# ── Directory-level vetter ─────────────────────────────────────────────────────

def vet_skill(skill_path: Path):
    """
    Vet a skill directory or a single SKILL.md file.

    Returns a result dict:
      status         : 'PASS' | 'WARN' | 'FAIL'
      skill_path     : str
      files_scanned  : [str, ...]
      findings       : {rel_path: {fails: [...], warns: [...]}}
      total_fails    : int
      total_warns    : int
    """
    result = {
        'skill_path': str(skill_path),
        'files_scanned': [],
        'findings': {},
        'total_fails': 0,
        'total_warns': 0,
        'status': 'PASS',
    }

    if not skill_path.exists():
        result['status'] = 'FAIL'
        result['findings']['_meta'] = {
            'fails': [(0, str(skill_path), "Path does not exist")],
            'warns': [],
        }
        result['total_fails'] = 1
        return result

    if skill_path.is_file():
        files_to_scan = [skill_path]
        base_dir = skill_path.parent
    else:
        files_to_scan = sorted(
            f for f in skill_path.rglob('*')
            if f.is_file() and f.suffix in SCAN_EXTENSIONS
        )
        base_dir = skill_path
        if not any(f.name == 'SKILL.md' for f in files_to_scan):
            result['findings']['_meta'] = {
                'fails': [],
                'warns': [(0, str(skill_path), "No SKILL.md found in directory")],
            }
            result['total_warns'] += 1

    for fpath in files_to_scan:
        try:
            rel = str(fpath.relative_to(base_dir))
        except ValueError:
            rel = fpath.name
        result['files_scanned'].append(rel)

        file_result = scan_file(fpath)
        if file_result['fails'] or file_result['warns']:
            result['findings'][rel] = file_result
        result['total_fails'] += len(file_result['fails'])
        result['total_warns'] += len(file_result['warns'])

    if result['total_fails'] > 0:
        result['status'] = 'FAIL'
    elif result['total_warns'] > 0:
        result['status'] = 'WARN'

    return result


def compute_sha256(path: Path) -> str:
    """Return SHA-256 hex digest of a file (for approved_skills.json manifest)."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# ── Human-readable report ─────────────────────────────────────────────────────

def print_report(result: dict) -> None:
    status = result['status']
    icon = {'PASS': '[PASS]', 'WARN': '[WARN]', 'FAIL': '[FAIL]'}.get(status, '[?]')
    sep = '=' * 62

    print(f"\n{sep}")
    print("  Cemini Agent Skill Vetting Report  —  Stage 1 Automated Scan")
    print(sep)
    print(f"  Skill    : {result['skill_path']}")
    print(f"  Scanned  : {len(result['files_scanned'])} file(s)")
    print(f"  Status   : {icon}")
    print(f"  Findings : {result['total_fails']} FAIL  |  {result['total_warns']} WARN")
    print(sep)

    if not result['findings']:
        print()
        print("  No issues detected.")
        print("  Proceed to Stage 2 manual audit before adding to approved_skills.json.")
        print()
        return

    print()
    for filename, fdata in result['findings'].items():
        for line_no, snippet, desc in fdata.get('fails', []):
            loc = f"L{line_no}" if line_no else "meta"
            print(f"  [FAIL] {filename}:{loc}")
            print(f"         {desc}")
            if snippet:
                print(f"         > {snippet}")
            print()

        for line_no, snippet, desc in fdata.get('warns', []):
            loc = f"L{line_no}" if line_no else "meta"
            print(f"  [WARN] {filename}:{loc}")
            print(f"         {desc}")
            if snippet:
                print(f"         > {snippet}")
            print()

    if status == 'FAIL':
        print(f"  {sep[:40]}")
        print("  VERDICT: DO NOT INSTALL this skill.")
        print("  Report to security@cemini and quarantine the skill directory.")
    elif status == 'WARN':
        print(f"  {sep[:40]}")
        print("  VERDICT: Proceed to Stage 2 manual audit before installation.")
    print()


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog='vet_skill',
        description='Cemini Stage 1 SKILL.md security scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Exit codes:  0=PASS  1=WARN  2=FAIL',
    )
    parser.add_argument('skill_path', help='Path to skill directory or SKILL.md file')
    parser.add_argument('--json', action='store_true',
                        help='Output JSON for CI integration (suppresses human report)')
    args = parser.parse_args()

    result = vet_skill(Path(args.skill_path))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)

    return {'PASS': 0, 'WARN': 1, 'FAIL': 2}.get(result['status'], 2)


if __name__ == '__main__':
    sys.exit(main())
