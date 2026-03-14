# License Compliance

Cemini Financial Suite is proprietary software. This page documents the license
compliance posture of all third-party dependencies.

---

## License Classification System

Dependencies are classified into three tiers:

| Tier | Licenses | Count | Risk |
|------|----------|-------|------|
| **Green** | MIT, Apache 2.0, BSD, ISC, PSF, MPL 2.0, Unlicense, Public Domain | ~95% | None |
| **Yellow** | LGPL (any variant) | ~10 packages | Low — isolation required |
| **Red** | GPL (pure, excluding LGPL) | 1 package | Medium — replacement recommended |

The full machine-readable classification is in `vdr/03_license_flags.json`.
The human-readable SBOM is in `vdr/02_sbom.md`.

---

## Green Tier (Permissive)

The overwhelming majority of Cemini's dependencies are permissive. Key examples:

| Package | License | Purpose |
|---------|---------|---------|
| FastAPI | MIT | API framework |
| Pydantic | MIT | Data validation |
| Redis-py | MIT | Cache/pub-sub client |
| psutil | BSD | System monitoring |
| APScheduler | MIT | Task scheduling |
| NumPy | BSD | Numerical computing |
| SciPy | BSD | Scientific computing |
| requests | Apache 2.0 | HTTP client |
| pandas | BSD | Data analysis |

---

## Yellow Tier (LGPL — Isolation Required)

LGPL packages require that:
1. The LGPL library is dynamically linked (not statically compiled into Cemini)
2. The end user can replace the LGPL library version without recompiling Cemini

Python's import mechanism satisfies both conditions. The LGPL API exception
explicitly permits calling LGPL code from non-LGPL applications.

| Package | License | Isolation Method |
|---------|---------|-----------------|
| psycopg2-binary | LGPL | Dynamic linking (C extension), standard practice |
| opentimestamps | LGPLv3+ | API caller only, no modifications |
| opentimestamps-client | LGPLv3+ | Subprocess isolation (CLI tool) |
| python-bitcoinlib | LGPLv3+ | Transitive dep, not directly imported |
| chardet | LGPL | Transitive dep, not directly imported |
| semgrep | LGPL-2.1+ | Dev-only — absent from all production containers |

See `vdr/04_isolation_report.md` for detailed analysis of each package.

---

## Red Tier (GPL — Replacement Recommended)

Only one pure-GPL package is present in the runtime environment:

### pymerkle (GPLv3+)

**Location:** `shared/audit_trail/merkle_batch.py`
**Use:** Merkle tree construction for the cryptographic audit trail (Layer 2)

**Current stance:** pymerkle is called via its public Python API. No source
modifications have been made. The standard library-use interpretation holds that
calling a GPL library's API from non-GPL code is permissible when no distribution
of the GPL library itself occurs.

**Conservative recommendation:** Replace pymerkle with a ~50-line stdlib implementation
using Python's built-in `hashlib`. This eliminates the only pure-GPL dependency.

```python
# Replacement sketch (stdlib only — MIT compatible)
import hashlib

def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return b""
    if len(leaves) == 1:
        return leaves[0]
    if len(leaves) % 2 == 1:
        leaves.append(leaves[-1])  # Duplicate last leaf
    parents = [
        hashlib.sha256(leaves[idx] + leaves[idx + 1]).digest()
        for idx in range(0, len(leaves), 2)
    ]
    return merkle_root(parents)
```

---

## How to Generate a Fresh SBOM

```bash
cd /opt/cemini
python3 scripts/license_audit.py
```

Outputs:
- `vdr/02_sbom.md` — Markdown table for human review
- `vdr/03_license_flags.json` — Machine-readable flags for automated checks
- `vdr/04_isolation_report.md` — Isolation analysis per flagged dependency

---

## Disclaimer

This compliance analysis is informational only. Cemini does not provide legal
advice. Buyers should obtain independent legal counsel to verify the compliance
posture before any commercialization or sale transaction, particularly regarding
pymerkle's GPLv3+ license.
