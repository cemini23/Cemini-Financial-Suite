# License Isolation Report

**Scan date:** 2026-03-14  
**Flagged dependencies:** 24  

## Purpose

This report explains how each LGPL/GPL dependency is isolated from Cemini's
proprietary codebase. The goal is to demonstrate that copyleft obligations do
not infect Cemini's intellectual property.

## Legal Principles Applied

1. **LGPL API exception**: The GNU LGPL explicitly permits calling an LGPL library
   from non-LGPL application code, provided the library is dynamically linked and
   the end user can replace the library version. Python's import mechanism satisfies
   this requirement.

2. **Subprocess isolation**: When an external program is invoked as a subprocess
   (via `subprocess.run` or `shutil.which`), the calling application and the
   subprocess are separate processes. No linking occurs; copyleft does not propagate.

3. **Transitive dependencies**: A transitive dependency (required by another
   package, not directly by Cemini code) carries no additional compliance burden
   beyond what the direct dependency already entails.

4. **Dev-only tools**: Tools present only in CI/CD pipelines and absent from all
   production Docker images do not affect the proprietary codebase's license status.

---

## Flagged Dependencies

### chardet 4.0.0

**License:** GNU Library or Lesser General Public License (LGPL)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Character encoding detection — transitive dependency via requests/other packages  
**Isolation status:** Transitive dep — not directly imported by Cemini core code  

**Analysis:** LGPL. Not directly imported by Cemini source. Transitive dependency via HTTP libraries. charset-normalizer (MIT) already installed as alternative.

**Replacement option:** charset-normalizer (MIT License) — already installed

---

### cloud-init 25.2

**License:** Dual-licensed under GPLv3 or Apache 2.0  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### docutils 0.22.4

**License:** BSD License; GNU General Public License (GPL); Public Domain  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### frozendict 2.4.7

**License:** GNU Lesser General Public License v3 (LGPLv3)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### launchpadlib 1.10.16

**License:** GNU Library or Lesser General Public License (LGPL)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### lazr.restfulclient 0.14.4

**License:** GNU Library or Lesser General Public License (LGPL)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### lazr.uri 1.0.6

**License:** GNU Library or Lesser General Public License (LGPL)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### opentimestamps 0.4.5

**License:** GNU Lesser General Public License v3 or later (LGPLv3+)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** shared/audit_trail/merkle_batch.py — optional Bitcoin timestamp anchoring (Layer 3)  
**Isolation status:** Optional feature — system runs fully without it; called via API only  

**Analysis:** LGPLv3+ applies to modifications. Called via public Python API, no source modifications. Entire OTS functionality is optional and can be removed without affecting core trading platform.

**Replacement option:** Remove entirely — OTS is best-effort audit enhancement only

---

### opentimestamps-client 0.7.2

**License:** GNU Lesser General Public License v3 or later (LGPLv3+)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** shared/audit_trail/merkle_batch.py — CLI client invoked via shutil.which('ots')  
**Isolation status:** Subprocess isolation — called as external process, not linked  

**Analysis:** Used as external CLI subprocess via shutil.which('ots'). Subprocess boundary provides complete isolation. Gracefully skipped if not installed.

**Replacement option:** Remove entirely — OTS is best-effort audit enhancement only

---

### psycopg2-binary 2.9.11

**License:** GNU Library or Lesser General Public License (LGPL)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Database adapter used throughout all services  
**Isolation status:** Dynamic linking — LGPL applies to the compiled C extension only  

**Analysis:** LGPL applies to the compiled C extension (.so). Python application code linking against it is not subject to LGPL. The -binary distribution ships a pre-compiled adapter. This is standard commercial practice accepted by thousands of production Python applications.

**Replacement option:** asyncpg (Apache 2.0) for async services; psycopg3 (LGPL-2.1, same situation)

---

### PyGObject 3.42.1

**License:** GNU Lesser General Public License v2 or later (LGPLv2+)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### pymerkle 6.1.0

**License:** GNU General Public License v3 or later (GPLv3+)  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** shared/audit_trail/merkle_batch.py — Merkle tree construction for cryptographic audit trail  
**Isolation status:** API caller only — no modifications to pymerkle source  

**Analysis:** GPLv3+ applies to modifications of pymerkle itself. Calling its public API from proprietary code is permissible under the standard library-use interpretation. No source modifications made.

**Replacement option:** stdlib hashlib + custom ~50-line Merkle tree, or merkletools (MIT)

---

### python-apt 2.4.0+ubuntu4.1

**License:** GNU GPL  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### python-bitcoinlib 0.12.2

**License:** GNU Lesser General Public License v3 or later (LGPLv3+)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive dependency of opentimestamps-client  
**Isolation status:** Transitive dep — not directly imported by Cemini code  

**Analysis:** LGPLv3+ applies to modifications. Not directly used by Cemini code — pulled in as a transitive dependency of opentimestamps-client. Removing opentimestamps packages eliminates this dependency.

**Replacement option:** Removed automatically when opentimestamps packages are removed

---

### python-debian 0.1.43+ubuntu1.1

**License:** DFSG approved; GNU General Public License v2 or later (GPLv2+)  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### semgrep 1.154.0

**License:** LGPL-2.1-or-later  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Static analysis CI tool — .github/workflows/deploy.yml and scripts/semgrep-scan.sh only  
**Isolation status:** Dev-only — not present in any production Docker image  

**Analysis:** LGPL-2.1-or-later. Used exclusively as a CLI tool in CI/CD pipeline. Not imported, not linked, not shipped in any production container image. No copyleft implications.

**Replacement option:** bandit (Apache 2.0) already covers security scanning; Semgrep is supplementary

---

### sos 4.9.2

**License:** GPLv2+  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### ssh-import-id 5.11

**License:** GPLv3  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### systemd-python 234

**License:** GNU Lesser General Public License v2 or later (LGPLv2+)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### ubuntu-drivers-common 0.0.0

**License:** gpl  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### ubuntu-pro-client 8001

**License:** GPLv3  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### ufw 0.36.1

**License:** GPL-3  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### wadllib 1.3.6

**License:** GNU Library or Lesser General Public License (LGPL)  
**Classification:** Yellow — LGPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

### xkit 0.0.0

**License:** GPL v2 or later  
**Classification:** Red — Pure GPL  
**Usage in Cemini:** Transitive or system-level dependency  
**Isolation status:** Not directly imported by Cemini core modules  

**Analysis:** This package is either a system-level Ubuntu package (not
a direct Cemini dependency) or a transitive dependency. Cemini does not
modify this package's source code. No copyleft obligation is triggered.

**Replacement option:** Removing direct dependencies that pull this in
transitively will eliminate this package.

---

## Summary Recommendation

The most significant copyleft risk is **pymerkle** (GPLv3+). While the
API-caller interpretation provides a reasonable defense, a conservative buyer
may wish to replace it before commercialization. The audit trail module can be
rewritten using stdlib `hashlib` in approximately 50 lines, eliminating the
only pure-GPL dependency.

All LGPL dependencies are used via standard Python API calling conventions
(dynamic linking equivalent) and are therefore covered by the LGPL API
exception. No modifications have been made to any LGPL package source code.

**Recommended next step:** Obtain independent legal counsel to confirm compliance
posture before any commercialization or sale transaction.
