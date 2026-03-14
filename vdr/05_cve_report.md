# CVE Security Audit Report

**Scan date:** 2026-03-14  
**Tool:** pip-audit 2.x (PyPI Advisory Database)  
**Total packages scanned:** 288  
**Vulnerabilities found:** 32  

## Vulnerability Summary

**32 vulnerability records** found across 9 packages.

> Note: Many of these may be in system-level Ubuntu packages or
> dev-only tools not present in production Docker images.
> Review each entry to determine applicability.

## Vulnerability Table

| CVE / Advisory ID | Package | Installed Version | Fix Version | Description |
|-------------------|---------|-------------------|-------------|-------------|
| CVE-2023-26112 (GHSA-c33w-24p9-8m24) | configobj | 5.0.6 | 5.0.9 | All versions of the package configobj are vulnerable to Regular Expression Denial of Service (ReDoS) via the validate fu... |
| CVE-2023-0286 (GHSA-x4qr-2fvf-3mr5) | cryptography | 3.4.8 | 39.0.1 | pyca/cryptography's wheels include a statically linked copy of OpenSSL. The versions of OpenSSL included in cryptography... |
| CVE-2023-50782 (GHSA-3ww4-gg4f-jr7f) | cryptography | 3.4.8 | 42.0.0 | A flaw was found in the python-cryptography package. This issue may allow a remote attacker to decrypt captured messages... |
| CVE-2024-0727 (GHSA-9v9h-cgj8-h64p) | cryptography | 3.4.8 | 42.0.2 | Issue summary: Processing a maliciously formatted PKCS12 file may lead OpenSSL to crash leading to a potential Denial of... |
| CVE-2026-26007 (GHSA-r6ph-v2qm-q3c2) | cryptography | 3.4.8 | 46.0.5 | ## Vulnerability Summary  The `public_key_from_numbers` (or `EllipticCurvePublicNumbers.public_key()`), `EllipticCurvePu... |
| GHSA-5cpq-8wj7-hf2v | cryptography | 3.4.8 | 41.0.0 | pyca/cryptography's wheels include a statically linked copy of OpenSSL. The versions of OpenSSL included in cryptography... |
| GHSA-jm77-qphf-c4w8 | cryptography | 3.4.8 | 41.0.3 | pyca/cryptography's wheels include a statically linked copy of OpenSSL. The versions of OpenSSL included in cryptography... |
| GHSA-v8gr-m533-ghj9 | cryptography | 3.4.8 | 41.0.4 | pyca/cryptography's wheels include a statically linked copy of OpenSSL. The versions of OpenSSL included in cryptography... |
| PYSEC-2023-11 (CVE-2023-23931) | cryptography | 3.4.8 | 39.0.1 | Previously, `Cipher.update_into` would accept Python objects which implement the buffer protocol, but provide only immut... |
| PYSEC-2023-11 (CVE-2023-23931) | cryptography | 3.4.8 | 39.0.1 | cryptography is a package designed to expose cryptographic primitives and recipes to Python developers. In affected vers... |
| PYSEC-2023-254 (CVE-2023-49083) | cryptography | 3.4.8 | 41.0.6 | ### Summary  Calling `load_pem_pkcs7_certificates` or `load_der_pkcs7_certificates` could lead to a NULL-pointer derefer... |
| PYSEC-2023-254 (CVE-2023-49083) | cryptography | 3.4.8 | 41.0.6 | cryptography is a package designed to expose cryptographic primitives and recipes to Python developers. Calling `load_pe... |
| PYSEC-2024-60 (GHSA-jjg7-2v4v-x38h) | idna | 3.3 | 3.7 | ### Impact A specially crafted argument to the `idna.encode()` function could consume significant resources. This may le... |
| PYSEC-2024-60 (CVE-2024-3651) | idna | 3.3 | 3.7 | A vulnerability was identified in the kjd/idna library, specifically within the `idna.encode()` function, affecting vers... |
| PYSEC-2022-269 (GHSA-3pgj-pg6c-r5p7) | oauthlib | 3.2.0 | 3.2.1 | OAuthLib is an implementation of the OAuth request-signing logic for Python 3.6+. In OAuthLib versions 3.1.1 until 3.2.1... |
| CVE-2025-8869 (BIT-pip-2025-8869) | pip | 22.0.2 | 25.3 | When extracting a tar archive pip may not check symbolic links point into the extraction directory if the tarfile module... |
| CVE-2026-1703 (BIT-pip-2026-1703) | pip | 22.0.2 | 26.0 | When pip is installing and extracting a maliciously crafted wheel archive, files may be extracted outside the installati... |
| PYSEC-2023-228 (CVE-2023-5752) | pip | 22.0.2 | 23.3 | When installing a package from a Mercurial VCS URL, e.g. `pip install hg+...`, with pip prior to v23.3, the specified Me... |
| PYSEC-2023-228 (CVE-2023-5752) | pip | 22.0.2 | 23.3 | When installing a package from a Mercurial VCS URL  (ie "pip install  hg+...") with pip prior to v23.3, the specified Me... |
| CVE-2026-32597 (GHSA-752w-5fwx-jx9f) | pyjwt | 2.11.0 | 2.12.0 | ## Summary  PyJWT does not validate the `crit` (Critical) Header Parameter defined in RFC 7515 §4.1.11. When a JWS token... |
| CVE-2024-6345 (BIT-setuptools-2024-6345) | setuptools | 59.6.0 | 70.0.0 | A vulnerability in the `package_index` module of pypa/setuptools versions up to 69.1.1 allows for remote code execution ... |
| PYSEC-2022-43012 (CVE-2022-40897) | setuptools | 59.6.0 | 65.5.1 | Python Packaging Authority (PyPA)'s setuptools is a library designed to facilitate packaging Python projects. Setuptools... |
| PYSEC-2022-43012 (CVE-2022-40897) | setuptools | 59.6.0 | 65.5.1 | Python Packaging Authority (PyPA) setuptools before 65.5.1 allows remote attackers to cause a denial of service via HTML... |
| PYSEC-2025-49 (CVE-2025-47273) | setuptools | 59.6.0 | 78.1.1 | ### Summary  A path traversal vulnerability in `PackageIndex` was fixed in setuptools version 78.1.1  ### Details ```   ... |
| PYSEC-2025-49 (CVE-2025-47273) | setuptools | 59.6.0 | 78.1.1 | setuptools is a package that allows users to download, build, install, upgrade, and uninstall Python packages. A path tr... |
| CVE-2022-39348 (GHSA-vg46-2rrj-3647) | twisted | 22.1.0 | 22.10.0rc1 | When the host header does not match a configured host, `twisted.web.vhost.NameVirtualHost` will return a `NoResource` re... |
| CVE-2024-41671 (GHSA-c8m8-j448-xjx7) | twisted | 22.1.0 | 24.7.0rc1 | ### Summary  The HTTP 1.0 and 1.1 server provided by twisted.web could process pipelined HTTP requests out-of-order, pos... |
| PYSEC-2022-160 (CVE-2022-21716) | twisted | 22.1.0 | 22.2.0 | Twisted is an event-based framework for internet applications, supporting Python 3.6+. Prior to 22.2.0, Twisted SSH clie... |
| PYSEC-2022-195 (GHSA-c2jg-hw38-jrqq) | twisted | 22.1.0 | 22.4.0 | Twisted is an event-based framework for internet applications, supporting Python 3.6+. Prior to version 22.4.0rc1, the T... |
| PYSEC-2023-224 (GHSA-xc8x-vp79-p3wm) | twisted | 22.1.0 | 23.10.0rc1 | Twisted is an event-based framework for internet applications. Prior to version 23.10.0rc1, when sending multiple HTTP r... |
| PYSEC-2024-75 (GHSA-cf56-g6w6-pqq2) | twisted | 22.1.0 | 24.7.0rc1 | Twisted is an event-based framework for internet applications, supporting Python 3.6+. The `twisted.web.util.redirectTo`... |
| PYSEC-2022-43017 (GHSA-qwmp-2cf2-g9g6) | wheel | 0.37.1 | 0.38.1 | An issue discovered in Python Packaging Authority (PyPA) Wheel 0.37.1 and earlier allows remote attackers to cause a den... |

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
