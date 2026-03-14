# Clean-Room Deployment Guide

This guide enables a buyer to deploy the Cemini Financial Suite on a fresh server
from scratch, starting only from the git repository and a `.env` file.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Ubuntu | 24.04 LTS | Other Debian-based distros may work |
| Docker | 24.0+ | Required for all services |
| Docker Compose | v2.0+ | Included with Docker Desktop / `docker-compose-plugin` |
| Python | 3.12 | For scripts and test suite |
| RAM | 16 GB+ | Grafana + Loki + Tempo are memory-intensive |
| Disk | 100 GB+ | `/mnt/archive/` for JSONL audit files |

---

## Step 1: Install Dependencies

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# Install Python 3.12
apt-get install -y python3.12 python3.12-venv python3-pip

# Install dbmate (schema migrations)
curl -fsSL -o /usr/local/bin/dbmate \
  https://github.com/amacneil/dbmate/releases/download/v2.31.0/dbmate-linux-amd64
chmod +x /usr/local/bin/dbmate

# Install MkDocs (optional — for documentation)
pip3 install mkdocs-material mkdocs-mermaid2-plugin
```

---

## Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/cemini23/Cemini-Financial-Suite.git /opt/cemini
cd /opt/cemini

# Copy environment template
cp .env.example .env

# Edit .env — configure all API keys (see comments in .env.example)
nano .env
```

**Required API keys (rotate before use):**

| Service | Variable | Source |
|---------|----------|--------|
| Alpaca (paper) | `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` | alpaca.markets |
| Kalshi | `KALSHI_API_KEY`, `KALSHI_CERT_PATH` | kalshi.com |
| Polygon.io | `POLYGON_API_KEY` | polygon.io |
| FRED | `FRED_API_KEY` | fred.stlouisfed.org |
| Visual Crossing | `VISUAL_CROSSING_KEY` | visualcrossing.com |
| Redis | `REDIS_PASSWORD` | Set any strong password |
| PostgreSQL | `POSTGRES_PASSWORD` | Set any strong password |

---

## Step 3: Run Database Migrations

```bash
cd /opt/cemini

# Start PostgreSQL first (needed for migrations)
docker compose up -d postgres

# Wait for PostgreSQL to be healthy
sleep 15

# Run all migrations
dbmate up

# Verify schema
docker exec cemini_postgres psql -U admin -d qdb -c "\dt"
```

---

## Step 4: Start All Services

```bash
cd /opt/cemini

# Build and start all ~26 services
docker compose up --build -d

# Wait for services to initialize
sleep 30

# Verify all containers are healthy
docker compose ps
```

**Expected output:** All containers showing `healthy` or `running` status.

---

## Step 5: Verify the Deployment

### Check service health

```bash
# Check all containers
docker compose ps

# Check logs for any startup errors
docker compose logs --tail=20 brain
docker compose logs --tail=20 quantos
docker compose logs --tail=20 kalshi
```

### Run the test suite

```bash
cd /opt/cemini
python3 -m pytest tests/ -v -n auto --timeout=60
```

Expected: 778+ tests passing, ~10 skipped.

### Check the Redis Intelligence Bus

```bash
docker exec cemini_redis redis-cli -a $REDIS_PASSWORD keys "intel:*"
```

Within 10 minutes of startup, you should see keys like:
`intel:vix_level`, `intel:spy_trend`, `intel:market_regime`, etc.

---

## Step 6: Verify the Audit Trail

```bash
# Create the archive directory
mkdir -p /mnt/archive/audit/chains /mnt/archive/audit/batches

# Run the offline verifier (will show 0 entries on fresh install — that's OK)
python3 scripts/verify.py --archive-root /mnt/archive/audit/
```

---

## Step 7: Build Documentation Site

```bash
cd /opt/cemini

# Build static site
mkdocs build --strict

# Verify build succeeded
ls site/index.html
```

---

## Step 8: Access the Platform

| Service | URL | Notes |
|---------|-----|-------|
| Grafana | `http://localhost:3000/grafana/` | admin/admin (change password) |
| QuantOS API | `http://localhost:8001/docs` | FastAPI Swagger UI |
| Kalshi API | `http://localhost:8000/docs` | FastAPI Swagger UI |
| MCP Server | `http://localhost:8002` | FastMCP tools |
| Performance Dashboard | `http://localhost:8501` | Streamlit |
| Portainer | `http://localhost:80/portainer/` | Docker management |
| pgAdmin | `http://localhost:5050` | Database management |

---

## Troubleshooting

### Services crash on startup
Check logs: `docker compose logs <service_name>`
Most common causes: missing `.env` variable, or database not yet ready.

### Test failures
```bash
python3 -m pytest tests/ -v --tb=short 2>&1 | grep FAILED
```

### Port conflicts
Edit `docker-compose.yml` to remap ports if any conflict with existing services.

### "No module named X" in tests
```bash
pip3 install -r requirements.txt
```

---

## API Key Rotation Checklist (Pre-Sale)

Before transferring the IP, rotate all API keys:

- [ ] Alpaca paper trading key
- [ ] Polygon.io key
- [ ] FRED API key
- [ ] Kalshi API key + PEM certificate
- [ ] Visual Crossing key
- [ ] Discord webhook URL
- [ ] GitHub deploy SSH key
- [ ] Grafana admin password
- [ ] Redis password
- [ ] PostgreSQL password

After rotation, update `.env` on the server and run `docker compose down && docker compose up -d`.
