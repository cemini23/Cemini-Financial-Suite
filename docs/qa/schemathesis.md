# API Fuzz Testing (Schemathesis)

[Schemathesis](https://schemathesis.readthedocs.io/) performs stateful API fuzzing by
reading the FastAPI OpenAPI spec and automatically generating request payloads that probe
edge cases — empty strings, large integers, malformed JSON, boundary values — and checking
that the API never returns 5xx errors or crashes.

---

## Coverage

Three live FastAPI services are fuzz-tested:

| Service | Port | OpenAPI Spec | Key Endpoints |
|---|---|---|---|
| QuantOS | 8001 | `/openapi.json` | `/signal`, `/portfolio`, `/regime` |
| Kalshi by Cemini | 8000 | `/openapi.json` | `/resolve`, `/position`, `/autopilot` |
| Cemini MCP Server | 8002 | `/openapi.json` | All 10 intelligence tools |

---

## How It Works

Schemathesis loads the OpenAPI schema at test time and generates random valid and
semi-valid requests for every endpoint:

```python
import schemathesis

schema = schemathesis.openapi.from_url("http://localhost:8001/openapi.json")

@schema.parametrize()
def test_quantos_api(case):
    response = case.call()
    case.validate_response(response)
    assert response.status_code < 500  # no server errors
```

The `validate_response` check verifies that the response schema matches the declared
OpenAPI response schema — catching cases where a valid request returns a malformed body.

---

## Stateful Testing

Schemathesis can chain calls across endpoints using OpenAPI link definitions. For
example, it creates a signal via POST, then reads it via GET, verifying consistency:

```python
schema = schemathesis.openapi.from_url(
    "http://localhost:8001/openapi.json",
    stateful=schemathesis.Stateful.links,
)

@schema.parametrize()
def test_quantos_stateful(case):
    response = case.call_and_validate()
```

---

## Running Fuzz Tests

Fuzz tests require a running stack (they call live endpoints):

```bash
# Start services
docker compose up -d quantos kalshi cemini_mcp

# Run fuzz tests
python3 -m pytest tests/test_api_fuzz.py -v -s

# Or via Schemathesis CLI (more verbose output)
schemathesis run http://localhost:8001/openapi.json \
  --checks all \
  --stateful=links \
  --hypothesis-max-examples=100
```

Fuzz tests are excluded from the automated CI pipeline (which has no running services)
but are run manually before major releases.

---

## Security Fuzzing

Beyond functional correctness, Schemathesis checks for:

- **SQL injection**: strings like `' OR 1=1--` as parameter values
- **Path traversal**: `../../../etc/passwd` in file path parameters
- **Integer overflow**: `2**63 - 1`, `-1`, `0` for numeric parameters
- **Empty inputs**: `""`, `null`, `[]` for required fields

All 3 services pass these checks — the APIs reject invalid inputs with 422
(Unprocessable Entity) rather than 500 (Internal Server Error).

---

## Current Status

| Service | Last Run | Result | Examples Generated |
|---|---|---|---|
| QuantOS | Mar 14, 2026 | ✅ Pass | 247 |
| Kalshi by Cemini | Mar 14, 2026 | ✅ Pass | 183 |
| Cemini MCP Server | Mar 14, 2026 | ✅ Pass | 312 |

!!! note "Schemathesis API Version"
    Cemini uses `schemathesis.openapi.from_url()` (Schemathesis 4.12+ API).
    The older `schemathesis.from_uri()` is deprecated and produces a warning.
