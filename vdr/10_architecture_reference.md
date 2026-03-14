# Architecture Reference

The complete technical architecture documentation is available as a MkDocs site
with 36 pages, Mermaid diagrams, and full navigation.

---

## How to Build the Documentation Site

```bash
cd /opt/cemini

# Install MkDocs and theme
pip install mkdocs-material mkdocs-mermaid2-plugin

# Build the static site (strict mode — fails on any warning)
mkdocs build --strict

# Output: site/ directory with 38+ HTML pages
```

### How to Serve Locally

```bash
mkdocs serve
# Opens at http://localhost:8000
```

---

## Key Documentation Pages

| Page | URL Path | Description |
|------|----------|-------------|
| System Overview | `/architecture/overview/` | High-level architecture with Mermaid diagrams |
| Docker Services | `/architecture/services/` | All 26 container services and their roles |
| Redis Intel Bus | `/architecture/redis-intel-bus/` | Channel map, TTL policies, pub/sub patterns |
| Signal Catalog | `/intelligence/signal-catalog/` | All 6 pattern detectors with detection logic |
| Macro Regime | `/intelligence/regime/` | GREEN/YELLOW/RED traffic-light model |
| Risk Engine | `/intelligence/risk-engine/` | Kelly Criterion, CVaR, Drawdown Monitor |
| Kill Switch | `/intelligence/kill-switch/` | CANCEL_ALL mechanism and triggers |
| Cryptographic Audit Trail | `/verification/audit-trail/` | 3-layer audit architecture diagram |
| Hash Chain Verification | `/verification/verify-script/` | Buyer verification script guide |
| OpenTimestamps | `/verification/opentimestamps/` | Bitcoin blockchain anchoring |
| Test Suite | `/qa/test-suite/` | 778+ tests, categories, parallel execution |
| CI/CD Pipeline | `/qa/ci-cd/` | 6-stage pipeline with Mermaid flowchart |
| Dependency Licenses | `/appendices/licenses/` | SBOM with LGPL/GPL isolation notes |
| Tech Debt Register | `/appendices/tech-debt/` | All known issues with severity |
| Due Diligence Overview | `/due-diligence/vdr-overview/` | VDR navigation guide |

---

## Architecture Diagrams Available

1. **System Overview** — Full service topology with network segments
2. **Data Pipeline** — Intelligence-in / ticker-out flow diagram
3. **Audit Trail Architecture** — 3-layer cryptographic chain
4. **Redis Intelligence Bus** — Channel map with direction arrows
5. **Regime Classification** — Traffic-light decision tree
6. **Risk Engine** — Kelly/CVaR/Drawdown pipeline
7. **Docker Networks** — edge_net / app_net / data_net segmentation
8. **CI/CD Pipeline** — 6-stage pipeline flowchart
9. **LGTM Observability** — Prometheus/Loki/Tempo/Grafana topology
10. **Pipeline Resilience** — Circuit breaker / retry / dead-letter queue
11. **Vector DB** — CRAG retrieval with pgvector
12. **EDGAR Pipeline** — SEC filing harvester architecture
13. **Opportunity Discovery** — Bayesian conviction scorer flow

All diagrams are rendered Mermaid (no external dependencies — renders in any
modern Markdown viewer or the MkDocs site).

---

## Source Code Structure

```
/opt/cemini/
├── agents/          # brain (orchestrator), analyzer, regime gate
├── ems/             # execution management system
├── QuantOS/         # equity/crypto signal engine (FastAPI)
├── Kalshi by Cemini/ # prediction market engine (FastAPI)
├── trading_playbook/ # observation-only playbook runner
├── opportunity_screener/ # discovery engine (FastAPI :8003)
├── cemini_mcp/      # MCP intelligence server (FastMCP :8002)
├── cemini_contracts/ # Pydantic v2 data contracts
├── logit_pricing/   # logit-space jump-diffusion pricing library
├── shared/          # shared utilities (intel_bus, audit_trail, resilience)
├── scrapers/        # data harvesters (GDELT, EDGAR, weather, social)
├── intelligence/    # pgvector + CRAG semantic retrieval layer
├── ui/              # Streamlit performance dashboard (:8501)
├── db/migrations/   # dbmate SQL migrations
├── monitoring/      # Prometheus/Loki/Alloy/Tempo/Grafana configs
├── scripts/         # audit, verification, and utility scripts
├── tests/           # 778+ pure unit tests
├── docs/            # MkDocs documentation source (36 pages)
└── vdr/             # Virtual Data Room (this directory)
```
