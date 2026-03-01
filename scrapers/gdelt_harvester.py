"""
GDELT Geopolitical Intelligence Harvester

Polls the GDELT 2.0 Event Database every 15 minutes (aligned with GDELT's update cadence).
Computes geopolitical risk scores and publishes to the Redis intel bus.
Stores scored events in Postgres (geopolitical_logs) + JSONL archives.

Data flow:
    GDELT 2.0 event stream (15-min export CSV, ~5-15 MB compressed)
        └─▶ filter: CAMEO 10-20 + market-relevant country actors
              └─▶ compute_risk_score() → 0-100
                    ├─▶ INSERT geopolitical_logs (Postgres, ELEVATED+ events only)
                    ├─▶ JSONL append /mnt/archive/geopolitical/
                    └─▶ SET intel:geopolitical_risk / intel:conflict_events /
                            intel:regional_risk (Redis)

No API key required — GDELT is fully open-access.
"""

import io
import json
import logging
import os
import time
import zipfile
from datetime import datetime, timezone

import pandas as pd
import psycopg2
import redis
import requests

try:
    from gdeltdoc import GdeltDoc, Filters as GdeltFilters
    _GDELT_DOC_AVAILABLE = True
except ImportError:
    _GDELT_DOC_AVAILABLE = False

logger = logging.getLogger("gdelt_harvester")

SCAN_INTERVAL = int(os.getenv("GDELT_SCAN_INTERVAL", "900"))

# GDELT 2.0 — last-update manifest (15-min refresh)
GDELT_V2_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# CAMEO root codes (2 digits) → geopolitical severity weight 0.0–1.0
# Higher weight = more significant / market-moving event type
CAMEO_SEVERITY = {
    "18": 1.00, "19": 1.00, "20": 1.00,   # Use of force / mass violence
    "14": 0.80, "15": 0.80, "16": 0.80, "17": 0.80,  # Protest, coerce, assault
    "10": 0.50, "11": 0.50, "12": 0.50, "13": 0.50,  # Demand, reject, threaten
    "06": 0.20, "07": 0.20, "08": 0.20, "09": 0.20,  # Cooperation (low risk)
    "01": 0.05, "02": 0.05, "03": 0.05, "04": 0.05, "05": 0.05,  # Diplomatic
}

# Only ingest events whose CAMEO root codes indicate high-impact activity
HIGH_IMPACT_CAMEO_ROOTS = frozenset({
    "10", "11", "12", "13",   # Demand, disapprove, reject, threaten
    "14", "15", "16", "17",   # Protest, reduce relations, coerce, assault
    "18", "19", "20",          # Unconventional force, military force, mass violence
})

CAMEO_CATEGORY = {
    "10": "Demand", "11": "Disapprove", "12": "Reject", "13": "Threaten",
    "14": "Protest", "15": "Reduce relations", "16": "Coerce", "17": "Assault",
    "18": "Unconventional force", "19": "Military force", "20": "Mass violence",
}

TRUSTED_DOMAINS = frozenset({
    "reuters.com", "apnews.com", "afp.com", "bbc.co.uk", "bbc.com",
    "nytimes.com", "washingtonpost.com", "theguardian.com", "ft.com",
    "economist.com", "wsj.com", "bloomberg.com", "cnbc.com",
    "defensenews.com", "foreignaffairs.com", "foreignpolicy.com",
    "cfr.org", "csis.org", "rand.org", "state.gov", "treasury.gov",
    "federalreserve.gov", "ecb.europa.eu", "imf.org", "worldbank.org",
    "aljazeera.com", "scmp.com", "japantimes.co.jp",
})

# Countries whose geopolitical events materially affect markets
MARKET_RELEVANT_COUNTRIES = frozenset({
    "US", "CN", "JP", "DE", "GB", "FR", "IN",
    "SA", "IR", "RU", "AE", "IQ", "VE", "NO",
    "UA", "TW", "KP", "IL", "PS", "SY",
    "MX", "CA", "KR", "BR", "AU",
})

REGION_MAP = {
    "CN": "asia_pacific", "JP": "asia_pacific", "TW": "asia_pacific",
    "KP": "asia_pacific", "KR": "asia_pacific", "AU": "asia_pacific", "IN": "asia_pacific",
    "SA": "middle_east", "IR": "middle_east", "IL": "middle_east", "PS": "middle_east",
    "AE": "middle_east", "IQ": "middle_east", "SY": "middle_east",
    "RU": "europe", "UA": "europe", "DE": "europe", "FR": "europe", "GB": "europe", "NO": "europe",
    "US": "americas", "CA": "americas", "MX": "americas", "BR": "americas", "VE": "americas",
}

# GDELT 2.0 export CSV: 61 tab-separated columns, no header
GDELT_V2_COLUMNS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_ADM2Code", "Actor1Geo_Lat", "Actor1Geo_Long",
    "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_ADM2Code", "Actor2Geo_Lat", "Actor2Geo_Long",
    "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_ADM2Code", "ActionGeo_Lat", "ActionGeo_Long",
    "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]


# ── Pure functions (no I/O, fully testable) ───────────────────────────────────

def get_cameo_root(cameo_code) -> str:
    """Return the normalised 2-digit CAMEO root code from any CAMEO code string."""
    if not cameo_code:
        return "01"
    code = str(cameo_code).strip()
    if not code:
        return "01"
    return (code[:2]).zfill(2) if len(code) >= 2 else code.zfill(2)


def is_trusted_source(domain: str) -> bool:
    """Return True if domain is in the curated trusted-source whitelist."""
    if not domain:
        return False
    d = domain.lower().strip()
    return d in TRUSTED_DOMAINS or any(d.endswith("." + t) for t in TRUSTED_DOMAINS)


def compute_risk_score(goldstein: float, num_sources: int, cameo_code: str, age_hours: float) -> float:
    """
    Compute a 0–100 geopolitical risk score for a single event.

    Weights:
      40 % — Goldstein severity  (-10 = max conflict → 100, +10 = cooperation → 0)
      25 % — Source confirmation  (linear up to 50 distinct sources)
      25 % — CAMEO event type    (severity weight from CAMEO_SEVERITY table)
      10 % — Recency             (exponential decay, half-life = 6 h)
    """
    goldstein_norm = max(0.0, min(100.0, ((-float(goldstein) + 10.0) / 20.0) * 100.0))
    source_score = min(100.0, (max(0, int(num_sources)) / 50.0) * 100.0)
    cameo_score = CAMEO_SEVERITY.get(get_cameo_root(cameo_code), 0.05) * 100.0
    recency_score = max(0.0, 100.0 * (0.5 ** (max(0.0, float(age_hours)) / 6.0)))
    raw = (0.40 * goldstein_norm + 0.25 * source_score
           + 0.25 * cameo_score + 0.10 * recency_score)
    return round(min(100.0, max(0.0, raw)), 1)


def classify_risk_level(score: float) -> str:
    """Classify a 0–100 risk score into CRITICAL / HIGH / ELEVATED / LOW."""
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "ELEVATED"
    return "LOW"


def compute_regional_risk(events: list) -> dict:
    """
    Aggregate risk scores by geographic region.
    Returns dict: {region: avg_score} for the four major regions.
    """
    buckets: dict = {
        "asia_pacific": [], "middle_east": [], "europe": [], "americas": [],
    }
    for ev in events:
        country = str(ev.get("action_geo") or ev.get("actor1_country") or "").strip()
        region = REGION_MAP.get(country, "")
        if region in buckets:
            buckets[region].append(float(ev.get("risk_score", 0.0)))
    return {
        region: round(sum(scores) / len(scores), 1) if scores else 0.0
        for region, scores in buckets.items()
    }


def score_event_row(row: dict, now_utc: datetime):
    """
    Score a single GDELT 2.0 event row (supplied as a plain dict).
    Returns a scored event dict, or None if the event is filtered out.

    Filters applied:
      - At least one actor / action geo must be a market-relevant country
      - CAMEO root code must be in HIGH_IMPACT_CAMEO_ROOTS (codes 10–20)
    """
    actor1 = str(row.get("Actor1CountryCode") or "").strip()
    actor2 = str(row.get("Actor2CountryCode") or "").strip()
    action_geo = str(row.get("ActionGeo_CountryCode") or "").strip()

    if not any(c in MARKET_RELEVANT_COUNTRIES for c in (actor1, actor2, action_geo)):
        return None

    cameo = str(row.get("EventCode") or "").strip()
    root = get_cameo_root(cameo)
    if root not in HIGH_IMPACT_CAMEO_ROOTS:
        return None

    # Safe numeric field parsing
    try:
        goldstein = float(row.get("GoldsteinScale") or 0)
    except (ValueError, TypeError):
        goldstein = 0.0
    try:
        num_sources = int(row.get("NumSources") or 0)
    except (ValueError, TypeError):
        num_sources = 0
    try:
        num_articles = int(row.get("NumArticles") or 0)
    except (ValueError, TypeError):
        num_articles = 0
    try:
        avg_tone = float(row.get("AvgTone") or 0)
    except (ValueError, TypeError):
        avg_tone = 0.0

    # Event date and age in hours
    try:
        date_str = str(row.get("SQLDATE") or "").strip()
        event_dt = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        age_hours = (now_utc - event_dt).total_seconds() / 3600.0
    except Exception:
        event_dt = now_utc
        age_hours = 1.0

    # Source URL and domain
    source_url = str(row.get("SOURCEURL") or "").strip()
    source_domain = ""
    if source_url:
        try:
            from urllib.parse import urlparse
            source_domain = urlparse(source_url).netloc.replace("www.", "")
        except Exception:
            pass

    risk_score = compute_risk_score(goldstein, num_sources, cameo, age_hours)
    category = CAMEO_CATEGORY.get(root, "Geopolitical event")
    actors = f"{actor1 or '?'}/{actor2 or '?'}" if actor2 else (actor1 or "?")
    title = f"{category} — {actors} [{action_geo or 'global'}]"

    return {
        "event_date": event_dt.isoformat(),
        "source_url": source_url[:500] or None,
        "source_domain": source_domain[:100] or None,
        "title": title[:250],
        "cameo_code": cameo[:10] or None,
        "cameo_category": category[:50],
        "goldstein_scale": goldstein,
        "avg_tone": avg_tone,
        "num_sources": num_sources,
        "num_articles": num_articles,
        "actor1_country": actor1[:5] or None,
        "actor2_country": actor2[:5] or None,
        "action_geo": action_geo[:5] or None,
        "risk_score": risk_score,
        "risk_level": classify_risk_level(risk_score),
        "themes": [],
        "payload": {
            "cameo": cameo, "goldstein": goldstein,
            "num_sources": num_sources, "actor1": actor1,
            "actor2": actor2, "action_geo": action_geo,
        },
    }


# ── I/O helpers ───────────────────────────────────────────────────────────────

def _get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=5432,
        dbname="qdb",
        user="admin",
        password=os.getenv("POSTGRES_PASSWORD", "quest"),
    )


def _get_redis_conn():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=6379,
        password=os.getenv("REDIS_PASSWORD", "cemini_redis_2026"),
        decode_responses=True,
    )


def _ensure_table(conn) -> None:
    """Create geopolitical_logs table and supporting indexes if they don't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS geopolitical_logs (
                id              SERIAL PRIMARY KEY,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                event_date      TIMESTAMPTZ,
                source_url      TEXT,
                source_domain   TEXT,
                title           TEXT,
                cameo_code      VARCHAR(10),
                cameo_category  VARCHAR(50),
                goldstein_scale FLOAT,
                avg_tone        FLOAT,
                num_sources     INTEGER,
                num_articles    INTEGER,
                actor1_country  VARCHAR(5),
                actor2_country  VARCHAR(5),
                action_geo      VARCHAR(5),
                risk_score      FLOAT,
                risk_level      VARCHAR(10),
                themes          JSONB,
                payload         JSONB
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_geo_logs_created "
            "ON geopolitical_logs(created_at DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_geo_logs_risk "
            "ON geopolitical_logs(risk_score DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_geo_logs_cameo "
            "ON geopolitical_logs(cameo_code)"
        )
        conn.commit()
    logger.info("[GDELT] geopolitical_logs table ready")


def _fetch_gdelt_v2_events() -> pd.DataFrame:
    """
    Download and parse the most recent GDELT 2.0 15-minute event export.
    Returns a named-column DataFrame, or empty DataFrame on any failure.
    """
    try:
        resp = requests.get(GDELT_V2_LASTUPDATE_URL, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"GDELT lastupdate.txt unreachable: {e}")
        return pd.DataFrame()

    events_url = None
    for line in resp.text.strip().splitlines():
        parts = line.split()
        if len(parts) >= 3 and "export.CSV.zip" in parts[2]:
            events_url = parts[2]
            break

    if not events_url:
        logger.warning("GDELT: export URL not found in lastupdate.txt")
        return pd.DataFrame()

    try:
        zip_resp = requests.get(events_url, timeout=90)
        zip_resp.raise_for_status()
    except Exception as e:
        logger.warning(f"GDELT event file download failed: {e}")
        return pd.DataFrame()

    try:
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as f:
                df = pd.read_csv(
                    f, sep="\t", header=None,
                    names=GDELT_V2_COLUMNS, dtype=str,
                    low_memory=False, on_bad_lines="skip",
                )
        logger.info(
            f"GDELT: downloaded {len(df)} raw events "
            f"from {events_url.split('/')[-1]}"
        )
        return df
    except Exception as e:
        logger.warning(f"GDELT CSV parse error: {e}")
        return pd.DataFrame()


def _fetch_gdelt_articles(timespan: str = "15min") -> list:
    """
    Query GDELT DOC API for recent geopolitical articles.
    Returns list of article dicts.  Returns [] if gdelt-doc-api unavailable.
    """
    if not _GDELT_DOC_AVAILABLE:
        return []

    geo_keywords = [
        "military sanctions conflict",
        "war invasion ceasefire",
        "nuclear weapons missile",
        "oil OPEC energy crisis",
    ]
    gd = GdeltDoc()
    articles = []
    for kw in geo_keywords:
        try:
            f = GdeltFilters(keyword=kw, timespan=timespan, num_records=25)
            result = gd.article_search(f)
            if result is not None and not result.empty:
                for _, row in result.iterrows():
                    tone_raw = row.get("tone")
                    articles.append({
                        "title": str(row.get("title", "")),
                        "url": str(row.get("url", "")),
                        "domain": str(row.get("domain", "")),
                        "tone": float(tone_raw) if pd.notna(tone_raw) else 0.0,
                    })
        except Exception as e:
            logger.debug(f"GDELT DOC API query failed for '{kw}': {e}")

    seen: set = set()
    unique = []
    for art in articles:
        if art["url"] not in seen:
            seen.add(art["url"])
            unique.append(art)
    return unique


def _publish_to_redis(r, events_scored: list) -> None:
    """Publish geopolitical risk summary and event list to the intel bus."""
    now_iso = datetime.now(timezone.utc).isoformat()
    _empty_regional = {
        "asia_pacific": 0.0, "middle_east": 0.0,
        "europe": 0.0, "americas": 0.0, "updated_at": now_iso,
    }

    if not events_scored:
        r.set("intel:geopolitical_risk", json.dumps({
            "score": 0.0, "level": "LOW", "top_event": "", "top_cameo": "",
            "num_high_impact_events": 0, "trend": "STABLE", "updated_at": now_iso,
        }))
        r.set("intel:conflict_events", json.dumps([]))
        r.set("intel:regional_risk", json.dumps(_empty_regional))
        return

    sorted_ev = sorted(events_scored, key=lambda e: e["risk_score"], reverse=True)
    top = sorted_ev[0]
    top_score = top["risk_score"]
    high_impact = [e for e in events_scored if e["risk_score"] >= 60]

    prev_raw = r.get("intel:geopolitical_risk")
    try:
        prev_score = json.loads(prev_raw).get("score", 0.0) if prev_raw else 0.0
    except Exception:
        prev_score = 0.0
    trend = (
        "RISING" if top_score > prev_score + 5
        else "FALLING" if top_score < prev_score - 5
        else "STABLE"
    )

    r.set("intel:geopolitical_risk", json.dumps({
        "score": top_score,
        "level": classify_risk_level(top_score),
        "top_event": top.get("title", ""),
        "top_cameo": top.get("cameo_code", ""),
        "num_high_impact_events": len(high_impact),
        "trend": trend,
        "updated_at": now_iso,
    }))

    r.set("intel:conflict_events", json.dumps([
        {
            "title": e["title"], "cameo_code": e["cameo_code"],
            "risk_score": e["risk_score"], "actor1": e["actor1_country"],
            "actor2": e["actor2_country"], "goldstein": e["goldstein_scale"],
            "sources": e["num_sources"], "event_date": e["event_date"],
        }
        for e in sorted_ev[:5]
    ]))

    regional = compute_regional_risk(events_scored)
    regional["updated_at"] = now_iso
    r.set("intel:regional_risk", json.dumps(regional))

    logger.info(
        f"🌍 Geo risk: {top_score} ({classify_risk_level(top_score)}) "
        f"| {len(events_scored)} events ({len(high_impact)} HIGH+) "
        f"| Trend: {trend} | Top: {top.get('title', '')[:60]}"
    )


def _write_to_postgres(conn, events: list) -> None:
    """Insert scored events into geopolitical_logs."""
    with conn.cursor() as cur:
        for ev in events:
            cur.execute(
                """
                INSERT INTO geopolitical_logs
                    (event_date, source_url, source_domain, title, cameo_code,
                     cameo_category, goldstein_scale, avg_tone, num_sources,
                     num_articles, actor1_country, actor2_country, action_geo,
                     risk_score, risk_level, themes, payload)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                     %s, %s, %s::jsonb, %s::jsonb)
                """,
                (
                    ev.get("event_date"), ev.get("source_url"), ev.get("source_domain"),
                    ev.get("title"), ev.get("cameo_code"), ev.get("cameo_category"),
                    ev.get("goldstein_scale"), ev.get("avg_tone"), ev.get("num_sources"),
                    ev.get("num_articles"), ev.get("actor1_country"), ev.get("actor2_country"),
                    ev.get("action_geo"), ev.get("risk_score"), ev.get("risk_level"),
                    json.dumps(ev.get("themes", [])), json.dumps(ev.get("payload", {})),
                ),
            )
        conn.commit()
    logger.info(f"📊 Inserted {len(events)} events into geopolitical_logs")


def _write_jsonl_archive(events: list) -> None:
    """Append scored events to a timestamped JSONL archive file."""
    archive_dir = "/mnt/archive/geopolitical"
    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    filepath = os.path.join(archive_dir, f"gdelt_{ts}.jsonl")
    with open(filepath, "w") as fh:
        for ev in events:
            fh.write(json.dumps(ev, default=str) + "\n")
    logger.info(f"📁 Archived {len(events)} events → {filepath}")


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )
    logger.info(f"🌍 GDELT Geopolitical Harvester starting (interval: {SCAN_INTERVAL}s)")

    conn = None
    r = None
    for attempt in range(30):
        try:
            conn = _get_db_conn()
            r = _get_redis_conn()
            r.ping()
            break
        except Exception as e:
            logger.warning(f"Startup retry {attempt + 1}/30: {e}")
            time.sleep(10)
    else:
        logger.error("❌ Could not connect to Postgres or Redis. Exiting.")
        return

    _ensure_table(conn)

    while True:
        cycle_start = time.time()
        try:
            now_utc = datetime.now(timezone.utc)

            # 1. Fetch GDELT 2.0 structured event stream
            df = _fetch_gdelt_v2_events()
            events_scored = []
            if not df.empty:
                for _, row_series in df.iterrows():
                    ev = score_event_row(row_series.to_dict(), now_utc)
                    if ev is not None:
                        events_scored.append(ev)

            logger.info(
                f"GDELT: {len(df)} raw rows → "
                f"{len(events_scored)} market-relevant events"
            )

            # 2. Publish to Redis intel bus (always — clears stale data on quiet cycles)
            try:
                _publish_to_redis(r, events_scored)
            except Exception as e:
                logger.error(f"Redis publish failed: {e}")
                try:
                    r = _get_redis_conn()
                except Exception:
                    pass

            # 3. Persist ELEVATED+ events (risk ≥ 40) to Postgres + JSONL
            elevated = [e for e in events_scored if e["risk_score"] >= 40]
            if elevated:
                try:
                    _write_to_postgres(conn, elevated)
                except Exception as e:
                    logger.error(f"Postgres write failed: {e}")
                    try:
                        conn = _get_db_conn()
                    except Exception:
                        pass
                try:
                    _write_jsonl_archive(elevated)
                except Exception as e:
                    logger.error(f"JSONL archive write failed: {e}")

        except Exception as e:
            logger.error(f"❌ GDELT cycle error: {e}", exc_info=True)
            try:
                conn = _get_db_conn()
                r = _get_redis_conn()
            except Exception:
                pass

        elapsed = time.time() - cycle_start
        sleep_time = max(0.0, SCAN_INTERVAL - elapsed)
        logger.info(f"🌍 Cycle complete in {elapsed:.1f}s | sleeping {sleep_time:.0f}s")
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
