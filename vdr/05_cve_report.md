# CVE Security Audit Report

**Scan date:** 2026-03-14  
**Tool:** pip-audit 2.x (PyPI Advisory Database)  
**Total packages scanned:** 292  
**Vulnerabilities found:** 18  

## Vulnerability Summary

**18 vulnerability records** found across 6 packages.

> Note: Many of these may be in system-level Ubuntu packages or
> dev-only tools not present in production Docker images.
> Review each entry to determine applicability.

## Vulnerability Table

| CVE / Advisory ID | Package | Installed Version | Fix Version | Description |
|-------------------|---------|-------------------|-------------|-------------|
| CVE-2023-26112 (GHSA-c33w-24p9-8m24) | configobj | 5.0.6 | 5.0.9 | All versions of the package configobj are vulnerable to Regular Expression Denial of Service (ReDoS) via the validate fu... |
| PYSEC-2022-269 (CVE-2022-36087) | oauthlib | 3.2.0 | 3.2.1 | OAuthLib is an implementation of the OAuth request-signing logic for Python 3.6+. In OAuthLib versions 3.1.1 until 3.2.1... |
| CVE-2025-8869 (BIT-pip-2025-8869) | pip | 22.0.2 | 25.3 | When extracting a tar archive pip may not check symbolic links point into the extraction directory if the tarfile module... |
| CVE-2026-1703 (BIT-pip-2026-1703) | pip | 22.0.2 | 26.0 | When pip is installing and extracting a maliciously crafted wheel archive, files may be extracted outside the installati... |
| PYSEC-2023-228 (CVE-2023-5752) | pip | 22.0.2 | 23.3 | When installing a package from a Mercurial VCS URL, e.g. `pip install hg+...`, with pip prior to v23.3, the specified Me... |
| PYSEC-2023-228 (CVE-2023-5752) | pip | 22.0.2 | 23.3 | When installing a package from a Mercurial VCS URL  (ie "pip install  hg+...") with pip prior to v23.3, the specified Me... |
| CVE-2024-6345 (BIT-setuptools-2024-6345) | setuptools | 59.6.0 | 70.0.0 | A vulnerability in the `package_index` module of pypa/setuptools versions up to 69.1.1 allows for remote code execution ... |
| PYSEC-2022-43012 (CVE-2022-40897) | setuptools | 59.6.0 | 65.5.1 | Python Packaging Authority (PyPA)'s setuptools is a library designed to facilitate packaging Python projects. Setuptools... |
| PYSEC-2022-43012 (CVE-2022-40897) | setuptools | 59.6.0 | 65.5.1 | Python Packaging Authority (PyPA) setuptools before 65.5.1 allows remote attackers to cause a denial of service via HTML... |
| PYSEC-2025-49 (GHSA-5rjg-fvgr-3xxf) | setuptools | 59.6.0 | 78.1.1 | ### Summary  A path traversal vulnerability in `PackageIndex` was fixed in setuptools version 78.1.1  ### Details ```   ... |
| PYSEC-2025-49 (GHSA-5rjg-fvgr-3xxf) | setuptools | 59.6.0 | 78.1.1 | setuptools is a package that allows users to download, build, install, upgrade, and uninstall Python packages. A path tr... |
| CVE-2022-39348 (GHSA-vg46-2rrj-3647) | twisted | 22.1.0 | 22.10.0rc1 | When the host header does not match a configured host, `twisted.web.vhost.NameVirtualHost` will return a `NoResource` re... |
| CVE-2024-41671 (GHSA-c8m8-j448-xjx7) | twisted | 22.1.0 | 24.7.0rc1 | ### Summary  The HTTP 1.0 and 1.1 server provided by twisted.web could process pipelined HTTP requests out-of-order, pos... |
| PYSEC-2022-160 (CVE-2022-21716) | twisted | 22.1.0 | 22.2.0 | Twisted is an event-based framework for internet applications, supporting Python 3.6+. Prior to 22.2.0, Twisted SSH clie... |
| PYSEC-2022-195 (GHSA-c2jg-hw38-jrqq) | twisted | 22.1.0 | 22.4.0 | Twisted is an event-based framework for internet applications, supporting Python 3.6+. Prior to version 22.4.0rc1, the T... |
| PYSEC-2023-224 (CVE-2023-46137) | twisted | 22.1.0 | 23.10.0rc1 | Twisted is an event-based framework for internet applications. Prior to version 23.10.0rc1, when sending multiple HTTP r... |
| PYSEC-2024-75 (CVE-2024-41810) | twisted | 22.1.0 | 24.7.0rc1 | Twisted is an event-based framework for internet applications, supporting Python 3.6+. The `twisted.web.util.redirectTo`... |
| PYSEC-2022-43017 (CVE-2022-40898) | wheel | 0.37.1 | 0.38.1 | An issue discovered in Python Packaging Authority (PyPA) Wheel 0.37.1 and earlier allows remote attackers to cause a den... |

## Remediation Notes

### Production Impact Assessment

The vulnerabilities above are in the full Python environment on the
development/server machine. Production Docker images use pinned
requirements and may not include all packages listed here.

To check which vulnerabilities affect production images, run:
```bash
pip-audit -r requirements.txt
pip-audit -r QuantOS/requirements.txt
pip-audit -r 'Kalshi by Cemini/requirements.txt'
```

### Upgrade Path

For each flagged package, run `pip install --upgrade <package>` and
verify tests still pass with `python3 -m pytest tests/ -n auto`.
