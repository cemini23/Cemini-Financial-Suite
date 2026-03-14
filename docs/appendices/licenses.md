# Dependency License Inventory

Generated via `pip-licenses --format=markdown --with-urls`. Last updated: March 14, 2026.

---

## Summary

The vast majority of Cemini's runtime dependencies are **MIT or Apache 2.0** licensed.
A small number of LGPL and GPL packages are present (see [Flagged Licenses](#flagged-licenses)
below); all are either system-level utilities (not part of the platform's IP) or
used in a way that does not trigger copyleft obligations.

**Core trading platform dependencies:** All MIT or Apache 2.0.

---

## Flagged Licenses

The following packages have non-permissive licenses. Each is annotated with the
isolation context:

| Package | Version | License | Isolation Notes |
|---|---|---|---|
| `pymerkle` | 6.1.0 | GPLv3+ | Used in `shared/audit_trail/` for Merkle tree construction. LGPL/GPL applies to modifications of pymerkle itself; calling its API from non-GPL code is permissible under the standard library-use interpretation. No modifications made. |
| `psycopg2-binary` | 2.9.11 | LGPL | Python database adapter. LGPL applies to the compiled C extension; Python code using it is not subject to LGPL. The `-binary` distribution includes the compiled adapter. Standard commercial practice. |
| `opentimestamps` | 0.4.5 | LGPLv3+ | Core OTS library. Called via API, not modified. |
| `opentimestamps-client` | 0.7.2 | LGPLv3+ | CLI client. Used as an external process via `shutil.which("ots")` — subprocess isolation. |
| `python-bitcoinlib` | 0.12.2 | LGPLv3+ | Bitcoin transaction library used by OTS. |
| `chardet` | 4.0.0 | LGPL | Character encoding detection. Called via API, not modified. |
| `semgrep` | 1.54.0 | LGPL-2.1+ | **Dev-only tool** — not included in production Docker images. |
| `frozendict` | 2.4.7 | LGPLv3 | Called via API, not modified. |
| `PyGObject` | 3.42.1 | LGPLv2+ | System library (Ubuntu), not a direct Cemini dependency. |
| `cloud-init` | 25.2 | GPLv3 or Apache 2.0 | Ubuntu system package, not a direct dependency. |
| `docutils` | 0.22.4 | BSD/GPL/Public Domain | Documentation tool, dev-only. |
| `python-apt` | 2.4.0 | GPL | Ubuntu system package, not a direct dependency. |

**Recommendation for buyer:** Obtain independent legal counsel to verify GPL/LGPL
compliance posture before commercialization, particularly regarding `pymerkle`. The
audit trail module could be rewritten using MIT-licensed alternatives (e.g., `merkletools`)
if copyleft isolation is a concern.

---

## Full Inventory

| Name | Version | License | URL |
|---|---|---|---|
| APScheduler | 3.11.2 | MIT | https://apscheduler.readthedocs.io |
| Authlib | 1.6.9 | BSD | https://github.com/authlib/authlib |
| aiobreaker | 1.2.0 | BSD | https://github.com/arlyon/aiobreaker |
| anyio | 4.12.1 | MIT | https://anyio.readthedocs.io |
| attrs | 25.4.0 | MIT | https://www.attrs.org |
| beartype | 0.22.9 | MIT | https://beartype.readthedocs.io |
| beautifulsoup4 | 4.14.3 | MIT | https://www.crummy.com/software/BeautifulSoup |
| certifi | 2026.1.4 | MPL 2.0 | https://github.com/certifi/python-certifi |
| charset-normalizer | 3.4.4 | MIT | https://github.com/jawah/charset_normalizer |
| click | 8.3.1 | BSD | https://palletsprojects.com/p/click |
| coverage | 7.13.4 | Apache 2.0 | https://github.com/coveragepy/coveragepy |
| cryptography | 3.4.8 | Apache/BSD | https://github.com/pyca/cryptography |
| fastapi | latest | MIT | https://fastapi.tiangolo.com |
| fastmcp | 3.1.0 | Apache 2.0 | https://gofastmcp.com |
| gdeltdoc | latest | MIT | https://github.com/alex9smith/gdelt-doc-api |
| hishel | latest | MIT | https://hishel.com |
| httpx | latest | BSD | https://www.python-httpx.org |
| hypothesis | latest | MPL 2.0 | https://hypothesis.readthedocs.io |
| Jinja2 | 3.1.6 | BSD | https://palletsprojects.com/p/jinja |
| mkdocs-material | latest | MIT | https://squidfunk.github.io/mkdocs-material |
| numpy | latest | BSD | https://numpy.org |
| opentelemetry-* | latest | Apache 2.0 | https://opentelemetry.io |
| opentimestamps | 0.4.5 | LGPLv3+ | https://github.com/opentimestamps |
| opentimestamps-client | 0.7.2 | LGPLv3+ | https://github.com/opentimestamps |
| pandas | latest | BSD | https://pandas.pydata.org |
| pgvector | latest | MIT | https://github.com/pgvector/pgvector-python |
| prometheus-client | latest | Apache 2.0 | https://github.com/prometheus/client_python |
| psycopg2-binary | 2.9.11 | LGPL | https://psycopg.org |
| pydantic | latest | MIT | https://docs.pydantic.dev |
| pymerkle | 6.1.0 | GPLv3+ | https://github.com/fmerg/pymerkle |
| PyYAML | 6.0.3 | MIT | https://pyyaml.org |
| redis | latest | MIT | https://github.com/redis/redis-py |
| ruff | latest | MIT | https://github.com/astral-sh/ruff |
| schemathesis | 4.12+ | MIT | https://schemathesis.readthedocs.io |
| scipy | latest | BSD | https://scipy.org |
| sentence-transformers | latest | Apache 2.0 | https://www.sbert.net |
| sqlalchemy | latest | MIT | https://www.sqlalchemy.org |
| starlette | latest | BSD | https://www.starlette.io |
| tenacity | latest | Apache 2.0 | https://tenacity.readthedocs.io |
| torch | latest | BSD | https://pytorch.org |
| transformers | latest | Apache 2.0 | https://huggingface.co/transformers |
| uvicorn | latest | BSD | https://www.uvicorn.org |
| uuid-utils | latest | MIT | https://github.com/bdraco/uuid-utils |
| websockets | 16.x | BSD | https://websockets.readthedocs.io |
| yfinance | latest | Apache 2.0 | https://github.com/ranaroussi/yfinance |

---

*For the authoritative full list, run: `pip-licenses --format=markdown --with-urls` in the project environment.*
