#!/usr/bin/env python3
"""
Cemini X Intelligence Harvester
================================
Burns ~$72 of remaining X API credits on targeted intelligence
harvesting before Netrows migration. Reserves $25 for ongoing bot.

Usage:
    python x_harvester.py search "Kalshi trading bot strategy"
    python x_harvester.py thread https://x.com/user/status/123456789
    python x_harvester.py account @SomeTrader --max-tweets 200
    python x_harvester.py sprint
    python x_harvester.py sprint --category prediction_markets
    python x_harvester.py budget
    python x_harvester.py analyze <harvest_file.jsonl>
    python x_harvester.py ls

Outputs:
    /mnt/archive/x_research/*.jsonl      -- Raw structured data
    /mnt/archive/x_research/claude/*.md  -- Claude-ready analysis
    /mnt/archive/x_research/budget.json  -- Spend tracker
    /mnt/archive/x_research/index.json   -- Master harvest index
"""

import argparse
import json
import os
import sys
import time
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("x_harvester")

# ── Config ────────────────────────────────────────────────────────
ARCHIVE_DIR = Path("/mnt/archive/x_research")
CLAUDE_DIR = ARCHIVE_DIR / "claude"
BUDGET_FILE = ARCHIVE_DIR / "budget.json"
INDEX_FILE = ARCHIVE_DIR / "index.json"

COST_PER_CALL = 0.03
HARVESTER_BUDGET = 75.0
RATE_LIMIT_SLEEP = 1.1
BASE_URL = "https://api.twitter.com/2"

TWEET_FIELDS = (
    "created_at,author_id,conversation_id,in_reply_to_user_id,"
    "referenced_tweets,public_metrics,entities,context_annotations"
)
USER_FIELDS = "name,username,description,public_metrics,verified"
EXPANSIONS = "author_id,referenced_tweets.id"

# ── Discovery queries ─────────────────────────────────────────────
DISCOVERY_QUERIES = {
    "prediction_markets": [
        "Kalshi bot strategy",
        "Kalshi trading algorithm",
        "prediction market arbitrage 2026",
        "prediction market bot profitable",
        "Kalshi weather market edge",
        "Polymarket Kalshi cross-platform arb",
        "prediction market API automation",
        "binary contract pricing model",
        "Kalshi API python trading",
        "event contract market making",
        "prediction market machine learning",
        "Kalshi order book analysis",
    ],
    "algo_trading": [
        "algorithmic trading edge 2026",
        "FinBERT sentiment trading results",
        "regime detection trading system",
        "Kelly criterion position sizing real",
        "CVaR risk management portfolio",
        "alternative data alpha signal",
        "SEC filing trading signal 8-K",
        "congressional trading tracker alpha",
        "reinforcement learning trading bot",
        "multi-agent trading ensemble LLM",
        "Docker trading infrastructure deploy",
        "Redis pub sub trading signal",
    ],
    "weather_commodity": [
        "weather derivative trading strategy",
        "NWS forecast arbitrage",
        "agricultural commodity weather model",
        "temperature prediction market Kalshi",
        "weather market profitable strategy",
        "commodity weather correlation alpha",
        "growing degree day trading",
        "energy weather forecast edge",
    ],
}

# ── Seed accounts ─────────────────────────────────────────────────
SEED_ACCOUNTS = [
    "0x_kaize",
    "0xMovez",
    "accuweather",
    "aleabitoreddit",
    "alex_prompter",
    "RyanMaue",
    "BigCheds",
    "BlueMoonTrades",
    "Bluntz_Capital",
    "BullflowIO",
    "ChartBreakouts",
    "ChartsJavi",
    "CheddarFlow",
    "dannycheng2022",
    "dunik_7",
    "economics",
    "epictrades1",
    "FelipeGuirao",
    "FL0WG0D",
    "hiddensmallcaps",
    "kingtutcap",
    "MartyChargin",
    "Maximus_Holla",
    "Mojo_flyin",
    "NOAA",
    "NOAA_HurrHunter",
    "NWS",
    "NWSMiami",
    "NWSNHC",
    "NWSSPC",
    "NWSWPC",
    "OneLouderApps",
    "Pentosh1",
    "prosperousguy",
    "prrobbins",
    "recogard",
    "ShardiB2",
    "WeatherBell",
    "spacexbt",
    "SunriseTrader",
    "TheProfInvestor",
    "TheShortBear",
    "TN_Finance",
    "TradetheMatrix1",
    "unusual_whales",
    "Venu_7_",
    "weatherchannel",
    "weathernetwork",
    "WisemanCap",
    "WSJmarkets",
    "_MiamiFL",
    # Tier 1 — Direct Pipeline Value (Quant/Finance/Real-time)
    "WatcherGuru",       # Breaking financial news, highest-velocity trigger
    "quantymacro",       # Quant macro, regime shift analysis
    "whale_alert",       # On-chain whale movement tracking
    "0xfdf",             # Market microstructure, quant math, Avellaneda-Stoikov
    # Tier 2 — Broader Value
    "systematicls",      # Systematic L/S equities, factor modeling
    "awealthofcs",       # Institutional portfolio mgmt, behavioral finance
    "bcherny",           # Claude Code creator, agent orchestration patterns
    "Web3Quant",         # Crypto quant signals, DeFi stat-arb models
    # Tier 3 — Agent/Ecosystem Intelligence
    "shawmakesmagic",    # ai16z, autonomous agent frameworks
    "_kaitoai",          # AI ecosystem adoption metrics
    "cookiedotfun",      # Agent swarm data, inter-agent schemas
]


# ── Budget tracker ────────────────────────────────────────────────
class BudgetTracker:
    def __init__(self):
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if BUDGET_FILE.exists():
            with open(BUDGET_FILE) as f:
                return json.load(f)
        return {
            "harvester_spent": 0.0,
            "harvester_calls": 0,
            "harvester_budget": HARVESTER_BUDGET,
            "started": datetime.now(timezone.utc).isoformat(),
            "last_call": None,
            "calls_by_type": {"search": 0, "thread": 0, "account": 0},
        }

    def _save(self):
        with open(BUDGET_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def can_spend(self) -> bool:
        return self.data["harvester_spent"] < self.data["harvester_budget"]

    def record_call(self, call_type: str = "search"):
        self.data["harvester_spent"] += COST_PER_CALL
        self.data["harvester_calls"] += 1
        self.data["last_call"] = datetime.now(timezone.utc).isoformat()
        ct = self.data["calls_by_type"]
        ct[call_type] = ct.get(call_type, 0) + 1
        self._save()

    @property
    def remaining(self) -> float:
        return self.data["harvester_budget"] - self.data["harvester_spent"]

    @property
    def calls_remaining(self) -> int:
        return int(self.remaining / COST_PER_CALL)

    def summary(self) -> str:
        d = self.data
        return (
            "\n"
            "============================================\n"
            "  X HARVESTER BUDGET STATUS\n"
            "============================================\n"
            f"  Spent:     ${d['harvester_spent']:.2f}"
            f" / ${d['harvester_budget']:.2f}\n"
            f"  Remaining: ${self.remaining:.2f}"
            f"  (~{self.calls_remaining} API calls)\n"
            f"  Total calls: {d['harvester_calls']}\n"
            f"    search:  {d['calls_by_type'].get('search', 0)}\n"
            f"    thread:  {d['calls_by_type'].get('thread', 0)}\n"
            f"    account: {d['calls_by_type'].get('account', 0)}\n"
            f"  Started:   {d.get('started', 'N/A')[:19]}\n"
            f"  Last call: {(d.get('last_call') or 'never')[:19]}\n"
            "============================================\n"
        )


# ── X API client ──────────────────────────────────────────────────
class XClient:
    def __init__(self, bearer_token: str, budget: BudgetTracker):
        self.budget = budget
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "CeminiHarvester/1.0",
        })

    def _get(self, endpoint: str, params: dict,
             call_type: str = "search") -> Optional[dict]:
        if not self.budget.can_spend():
            log.warning("Budget exhausted. Stopping.")
            return None
        url = f"{BASE_URL}/{endpoint}"
        time.sleep(RATE_LIMIT_SLEEP)
        try:
            resp = self.session.get(url, params=params, timeout=30)
            self.budget.record_call(call_type)
            if resp.status_code == 429:
                reset = int(resp.headers.get("x-rate-limit-reset", 0))
                wait = max(reset - int(time.time()), 15)
                log.warning(f"Rate limited. Sleeping {wait}s...")
                time.sleep(wait + 1)
                return self._get(endpoint, params, call_type)
            if resp.status_code != 200:
                log.error(f"API {resp.status_code}: {resp.text[:200]}")
                return None
            return resp.json()
        except requests.RequestException as e:
            log.error(f"Request failed: {e}")
            return None

    def search_recent(self, query: str, max_results: int = 10,
                      next_token: str = None) -> Optional[dict]:
        params = {
            "query": f"{query} -is:retweet lang:en",
            "max_results": min(max(10, max_results), 100),
            "tweet.fields": TWEET_FIELDS,
            "user.fields": USER_FIELDS,
            "expansions": EXPANSIONS,
            "sort_order": "relevancy",
        }
        if next_token:
            params["next_token"] = next_token
        return self._get("tweets/search/recent", params, "search")

    def get_tweet(self, tweet_id: str) -> Optional[dict]:
        params = {
            "tweet.fields": TWEET_FIELDS,
            "user.fields": USER_FIELDS,
            "expansions": EXPANSIONS,
        }
        return self._get(f"tweets/{tweet_id}", params, "thread")

    def get_conversation(self, conversation_id: str,
                         max_results: int = 100) -> Optional[dict]:
        params = {
            "query": f"conversation_id:{conversation_id}",
            "max_results": min(max(10, max_results), 100),
            "tweet.fields": TWEET_FIELDS,
            "user.fields": USER_FIELDS,
            "expansions": EXPANSIONS,
            "sort_order": "recency",
        }
        return self._get("tweets/search/recent", params, "thread")

    def get_user_by_username(self, username: str) -> Optional[dict]:
        username = username.lstrip("@")
        params = {"user.fields": USER_FIELDS}
        return self._get(
            f"users/by/username/{username}", params, "account"
        )

    def get_user_tweets(self, user_id: str, max_results: int = 100,
                        next_token: str = None) -> Optional[dict]:
        params = {
            "max_results": min(max(10, max_results), 100),
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "exclude": "retweets",
        }
        if next_token:
            params["pagination_token"] = next_token
        return self._get(
            f"users/{user_id}/tweets", params, "account"
        )


# ── Tweet enrichment ──────────────────────────────────────────────
def _user_map(response: dict) -> dict:
    users = {}
    if response and "includes" in response:
        for u in response["includes"].get("users", []):
            users[u["id"]] = {
                "name": u.get("name", ""),
                "username": u.get("username", ""),
                "description": u.get("description", ""),
                "followers": u.get(
                    "public_metrics", {}
                ).get("followers_count", 0),
                "verified": u.get("verified", False),
            }
    return users


def _enrich_tweet(tweet: dict, users: dict) -> dict:
    author = users.get(tweet.get("author_id", ""), {})
    metrics = tweet.get("public_metrics", {})
    engagement = (
        metrics.get("like_count", 0) * 1
        + metrics.get("retweet_count", 0) * 3
        + metrics.get("reply_count", 0) * 2
        + metrics.get("quote_count", 0) * 4
    )
    followers = author.get("followers", 0)
    engagement_normalized = round(engagement / max(followers, 1) * 10000, 2)
    return {
        "id": tweet["id"],
        "text": tweet.get("text", ""),
        "created_at": tweet.get("created_at", ""),
        "author_id": tweet.get("author_id", ""),
        "author_name": author.get("name", ""),
        "author_username": author.get("username", ""),
        "author_followers": author.get("followers", 0),
        "conversation_id": tweet.get("conversation_id", ""),
        "metrics": metrics,
        "engagement_score": engagement,
        "engagement_normalized": engagement_normalized,
        "entities": tweet.get("entities", {}),
        "context_annotations": tweet.get("context_annotations", []),
        "referenced_tweets": tweet.get("referenced_tweets", []),
    }


# ── Storage ───────────────────────────────────────────────────────
def save_harvest(tweets: list, label: str,
                 metadata: dict = None) -> Optional[Path]:
    if not tweets:
        log.warning("No tweets to save.")
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_label = re.sub(r"[^a-zA-Z0-9_-]", "_", label)[:60]
    filename = f"harvest_{ts}_{safe_label}.jsonl"
    filepath = ARCHIVE_DIR / filename

    tweets.sort(
        key=lambda t: t.get("engagement_score", 0), reverse=True
    )
    with open(filepath, "w") as f:
        for t in tweets:
            f.write(json.dumps(t, default=str) + "\n")

    index = []
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            index = json.load(f)
    index.append({
        "file": filename,
        "label": label,
        "tweet_count": len(tweets),
        "harvested_at": datetime.now(timezone.utc).isoformat(),
        "top_engagement": tweets[0]["engagement_score"] if tweets else 0,
        "top_author": tweets[0].get("author_username", "") if tweets else "",
        "metadata": metadata or {},
    })
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

    log.info(f"Saved {len(tweets)} tweets -> {filepath.name}")
    return filepath


# ── Harvest operations ────────────────────────────────────────────
def harvest_search(client: XClient, query: str,
                   max_tweets: int = 50,
                   seen_ids: set = None) -> list:
    """Search tweets. Skips any tweet ID already in seen_ids."""
    if seen_ids is None:
        seen_ids = set()
    log.info(f"[search] '{query}' (max {max_tweets})")
    all_tweets = []
    next_token = None
    pages = 0
    max_pages = max(1, max_tweets // 10)

    while pages < max_pages and client.budget.can_spend():
        batch = min(max_tweets - len(all_tweets), 100)
        if batch < 10:
            batch = 10
        result = client.search_recent(
            query, max_results=batch, next_token=next_token
        )
        if not result or "data" not in result:
            break
        users = _user_map(result)
        for tweet in result["data"]:
            if tweet["id"] not in seen_ids:
                seen_ids.add(tweet["id"])
                all_tweets.append(_enrich_tweet(tweet, users))
        next_token = result.get("meta", {}).get("next_token")
        pages += 1
        if not next_token or len(all_tweets) >= max_tweets:
            break

    log.info(f"  -> {len(all_tweets)} new tweets")
    return all_tweets


def harvest_thread(client: XClient, tweet_id: str,
                   seen_ids: set = None) -> list:
    """Harvest a conversation thread. Deduplicates via seen_ids."""
    if seen_ids is None:
        seen_ids = set()
    match = re.search(r"/status/(\d+)", str(tweet_id))
    if match:
        tweet_id = match.group(1)

    log.info(f"[thread] tweet {tweet_id}")
    root_resp = client.get_tweet(tweet_id)
    if not root_resp or "data" not in root_resp:
        log.error(f"Could not fetch tweet {tweet_id}")
        return []

    root_tweet = root_resp["data"]
    conv_id = root_tweet.get("conversation_id", tweet_id)
    users = _user_map(root_resp)
    all_tweets = []

    if root_tweet["id"] not in seen_ids:
        seen_ids.add(root_tweet["id"])
        all_tweets.append(_enrich_tweet(root_tweet, users))

    conv_resp = client.get_conversation(conv_id, max_results=100)
    if conv_resp and "data" in conv_resp:
        conv_users = _user_map(conv_resp)
        for tweet in conv_resp["data"]:
            if tweet["id"] not in seen_ids:
                seen_ids.add(tweet["id"])
                all_tweets.append(_enrich_tweet(tweet, conv_users))

    log.info(f"  -> {len(all_tweets)} new tweets in thread")
    return all_tweets


def harvest_account(client: XClient, username: str,
                    max_tweets: int = 200,
                    seen_ids: set = None) -> list:
    """Pull recent tweets from an account. Deduplicates via seen_ids."""
    if seen_ids is None:
        seen_ids = set()
    username = username.lstrip("@")
    log.info(f"[account] @{username} (max {max_tweets})")

    user_resp = client.get_user_by_username(username)
    if not user_resp or "data" not in user_resp:
        log.error(f"Could not find @{username}")
        return []

    user_data = user_resp["data"]
    user_id = user_data["id"]
    followers = user_data.get(
        "public_metrics", {}
    ).get("followers_count", 0)
    log.info(f"  Found: {user_data.get('name', '')} ({followers} followers)")

    all_tweets = []
    next_token = None
    pages = 0
    max_pages = max(1, max_tweets // 100)

    while pages < max_pages and client.budget.can_spend():
        batch = min(100, max_tweets - len(all_tweets))
        if batch < 10:
            batch = 10
        result = client.get_user_tweets(
            user_id, max_results=batch, next_token=next_token
        )
        if not result or "data" not in result:
            break
        users = _user_map(result)
        users[user_id] = {
            "name": user_data.get("name", ""),
            "username": user_data.get("username", username),
            "description": user_data.get("description", ""),
            "followers": followers,
            "verified": user_data.get("verified", False),
        }
        for tweet in result["data"]:
            if tweet["id"] not in seen_ids:
                seen_ids.add(tweet["id"])
                all_tweets.append(_enrich_tweet(tweet, users))
        next_token = result.get("meta", {}).get("next_token")
        pages += 1
        if not next_token or len(all_tweets) >= max_tweets:
            break

    log.info(f"  -> {len(all_tweets)} new tweets from @{username}")
    return all_tweets


# ── Sprint ────────────────────────────────────────────────────────
def run_sprint(client: XClient, budget: BudgetTracker,
               categories: list = None):
    """
    3-phase auto-discovery sprint with global deduplication.

    Phase 1 (50%): Search queries across categories
    Phase 2 (30%): Deep-pull seed accounts
    Phase 3 (20%): Expand highest-engagement threads
    """
    if categories is None:
        categories = list(DISCOVERY_QUERIES.keys())

    total = budget.remaining
    p1_limit = total * 0.50
    p2_limit = total * 0.30

    # Global dedup sets — shared across ALL phases
    seen_tweet_ids = set()
    seen_conversation_ids = set()

    log.info("=" * 50)
    log.info("  INTELLIGENCE SPRINT")
    log.info("=" * 50)
    log.info(f"  Budget:   ${total:.2f}")
    log.info(f"  Phase 1 (search):   ~${p1_limit:.2f}")
    log.info(f"  Phase 2 (accounts): ~${p2_limit:.2f}")
    log.info(f"  Phase 3 (threads):  ~${total - p1_limit - p2_limit:.2f}")
    log.info(f"  Categories: {', '.join(categories)}")
    log.info(f"  Seed accounts: {len(SEED_ACCOUNTS)}")
    log.info("")

    high_engagement = []

    # ── Phase 1: Search ───────────────────────────────────────
    log.info("--- PHASE 1: SEARCH DISCOVERY ---")
    p1_start = budget.data["harvester_spent"]

    for cat in categories:
        if cat not in DISCOVERY_QUERIES:
            continue
        queries = DISCOVERY_QUERIES[cat]
        log.info(f"\nCategory: {cat} ({len(queries)} queries)")

        for query in queries:
            if (budget.data["harvester_spent"] - p1_start) >= p1_limit:
                log.info("Phase 1 budget reached.")
                break
            if not budget.can_spend():
                break

            tweets = harvest_search(
                client, query, max_tweets=30,
                seen_ids=seen_tweet_ids
            )
            if tweets:
                save_harvest(
                    tweets, f"search_{cat}",
                    {"query": query, "category": cat, "phase": 1}
                )
                for t in tweets:
                    if t["engagement_score"] >= 30:
                        high_engagement.append(t)

    p1_tweets = len(seen_tweet_ids)
    log.info(f"\nPhase 1 complete: {p1_tweets} unique tweets")

    # ── Phase 2: Seed accounts ────────────────────────────────
    log.info("\n--- PHASE 2: ACCOUNT DEEP-PULL ---")
    log.info(f"  {len(SEED_ACCOUNTS)} accounts to harvest")
    p2_start = budget.data["harvester_spent"]

    for username in SEED_ACCOUNTS:
        if (budget.data["harvester_spent"] - p2_start) >= p2_limit:
            log.info("Phase 2 budget reached.")
            break
        if not budget.can_spend():
            break

        tweets = harvest_account(
            client, username, max_tweets=100,
            seen_ids=seen_tweet_ids
        )
        if tweets:
            save_harvest(
                tweets, f"account_{username}",
                {"username": username, "phase": 2}
            )
            for t in tweets:
                if t["engagement_score"] >= 30:
                    high_engagement.append(t)

    p2_new = len(seen_tweet_ids) - p1_tweets
    log.info(f"\nPhase 2 complete: {p2_new} new unique tweets")

    # ── Phase 3: Thread expansion ─────────────────────────────
    log.info("\n--- PHASE 3: THREAD EXPANSION ---")

    # Deduplicate threads by conversation_id
    unique_threads = []
    for t in sorted(high_engagement,
                    key=lambda x: x["engagement_score"],
                    reverse=True):
        conv_id = t.get("conversation_id", t["id"])
        if conv_id not in seen_conversation_ids:
            seen_conversation_ids.add(conv_id)
            unique_threads.append(t)

    log.info(
        f"  {len(unique_threads)} unique high-engagement threads "
        f"(deduped from {len(high_engagement)} candidates)"
    )

    expanded = 0
    for t in unique_threads[:50]:
        if not budget.can_spend():
            break
        thread_tweets = harvest_thread(
            client, t["id"], seen_ids=seen_tweet_ids
        )
        if thread_tweets and len(thread_tweets) > 1:
            save_harvest(
                thread_tweets,
                f"thread_{t.get('author_username', 'unknown')}",
                {
                    "root_tweet_id": t["id"],
                    "root_engagement": t["engagement_score"],
                    "author": t.get("author_username", ""),
                    "phase": 3,
                }
            )
            expanded += 1

    log.info(f"\nPhase 3 complete: {expanded} threads expanded")

    # ── Summary ───────────────────────────────────────────────
    log.info("")
    log.info("=" * 50)
    log.info("  SPRINT COMPLETE")
    log.info("=" * 50)
    log.info(f"  Total unique tweets: {len(seen_tweet_ids)}")
    log.info(f"  Unique threads expanded: {expanded}")
    log.info(f"  Conversation IDs tracked: {len(seen_conversation_ids)}")
    log.info(budget.summary())

    _generate_sprint_summary()


def _generate_sprint_summary():
    """Auto-generate combined Claude-ready markdown of best finds."""
    if not INDEX_FILE.exists():
        return
    with open(INDEX_FILE) as f:
        index = json.load(f)

    all_tweets = []
    for entry in index:
        fp = ARCHIVE_DIR / entry["file"]
        if fp.exists():
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        t = json.loads(line)
                        t["_source_file"] = entry["file"]
                        t["_category"] = entry.get(
                            "metadata", {}
                        ).get("category", "unknown")
                        all_tweets.append(t)

    # Deduplicate by tweet ID
    seen = set()
    unique = []
    for t in all_tweets:
        if t["id"] not in seen:
            seen.add(t["id"])
            unique.append(t)

    for t in unique:
        raw = t.get("engagement_score", 0)
        norm = t.get("engagement_normalized", 0)
        if t.get("author_followers", 0) < 500 or raw < 10:
            norm = 0
        t["_blended_rank"] = (raw * 0.4) + (norm * 0.6)
    unique.sort(key=lambda t: t.get("_blended_rank", 0), reverse=True)
    top = unique[:150]

    lines = [
        "# X Intelligence Sprint - Combined Analysis",
        f"**Generated:** "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Total unique tweets:** {len(unique)}",
        f"**Showing top:** {len(top)} by engagement",
        f"**Harvest files:** {len(index)}",
        "",
        "---",
        "",
        "## Analysis Instructions for Claude",
        "",
        "This is harvested X/Twitter intelligence for the Cemini "
        "Financial Suite. Three engines: Root (LangGraph orchestrator), "
        "QuantOS (equities/crypto), Kalshi by Cemini (prediction markets). "
        "Current phase: data accumulation / paper mode.",
        "",
        "Extract and organize:",
        "1. **Architecture patterns** -- bot designs, infra choices",
        "2. **Trading strategies** -- specific edges, microstructure",
        "3. **Data sources** -- APIs, datasets, feeds mentioned",
        "4. **Risk patterns** -- failures and mistakes to avoid",
        "5. **Cemini roadmap mapping** -- map to Steps 3-30",
        "",
        "Categorize: IMMEDIATE / SHORT-TERM / MEDIUM-TERM.",
        "",
        "---",
        "",
    ]

    by_cat = {}
    for t in top:
        cat = t.get("_category", "general")
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(t)

    for cat, tweets in by_cat.items():
        lines.append(f"## Category: {cat}")
        lines.append("")
        for tweet in tweets[:50]:
            eng = tweet.get("engagement_score", 0)
            norm = tweet.get("engagement_normalized", 0)
            m = tweet.get("metrics", {})
            author = tweet.get("author_username", "unknown")
            followers = tweet.get("author_followers", 0)
            text = tweet.get("text", "").replace("\n", "\n> ")
            lines.extend([
                f"### @{author} "
                f"({followers:,} followers | engagement: {eng} | normalized: {norm})",
                f"Likes: {m.get('like_count', 0)} | "
                f"RTs: {m.get('retweet_count', 0)} | "
                f"Replies: {m.get('reply_count', 0)} | "
                f"Quotes: {m.get('quote_count', 0)}  ",
                f"Posted: {tweet.get('created_at', 'N/A')[:19]}",
                "", f"> {text}", "", "---", "",
            ])

    summary_path = CLAUDE_DIR / "sprint_analysis.md"
    with open(summary_path, "w") as f:
        f.write("\n".join(lines))
    log.info(f"Sprint summary: {summary_path}")
    log.info("Feed to Claude Code:")
    log.info(f"  cat {summary_path} | claude")


# ── Single-file Claude analysis ──────────────────────────────────
def generate_claude_markdown(filepath: Path) -> str:
    if not filepath.exists():
        filepath = ARCHIVE_DIR / filepath
    if not filepath.exists():
        filepath = ARCHIVE_DIR / Path(str(filepath)).name
    if not filepath.exists():
        return f"ERROR: File not found: {filepath}"

    tweets = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                tweets.append(json.loads(line))
    if not tweets:
        return "ERROR: No tweets in file."

    for t in tweets:
        raw = t.get("engagement_score", 0)
        norm = t.get("engagement_normalized", 0)
        if t.get("author_followers", 0) < 500 or raw < 10:
            norm = 0
        t["_blended_rank"] = (raw * 0.4) + (norm * 0.6)
    tweets.sort(key=lambda t: t.get("_blended_rank", 0), reverse=True)

    lines = [
        f"# X Intelligence Harvest: {filepath.stem}",
        f"**Source:** `{filepath.name}`",
        f"**Tweets:** {len(tweets)}",
        f"**Generated:** "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "", "---", "",
        "## Analysis Instructions",
        "",
        "Analyze for Cemini Financial Suite (algo trading platform "
        "with Kalshi prediction market, equity, and crypto engines). "
        "Extract:",
        "1. **Architecture patterns** for bot/system design",
        "2. **Strategy insights** -- edges, microstructure",
        "3. **Data source leads** -- APIs, datasets, feeds",
        "4. **Risk/failure patterns** -- avoid their mistakes",
        "5. **Cemini improvements** -- map to Steps 3-30",
        "", "---", "",
    ]

    for i, tweet in enumerate(tweets[:100]):
        eng = tweet.get("engagement_score", 0)
        m = tweet.get("metrics", {})
        author = tweet.get("author_username", "unknown")
        followers = tweet.get("author_followers", 0)
        text = tweet.get("text", "").replace("\n", "\n> ")
        lines.extend([
            f"### Tweet {i+1} -- @{author} "
            f"({followers:,} followers, engagement: {eng})",
            f"Likes: {m.get('like_count', 0)} | "
            f"RTs: {m.get('retweet_count', 0)} | "
            f"Replies: {m.get('reply_count', 0)} | "
            f"Quotes: {m.get('quote_count', 0)}  ",
            f"Posted: {tweet.get('created_at', 'N/A')[:19]}",
            "", f"> {text}", "", "---", "",
        ])

    lines.extend([
        "## Summary Request", "",
        "Provide:",
        "1. **Top 5 actionable findings** with Cemini step references",
        "2. **New accounts to monitor**",
        "3. **Strategies worth investigating**",
        "4. **Warnings** about failed approaches",
    ])
    return "\n".join(lines)


# ── Token resolution ──────────────────────────────────────────────
def get_bearer_token() -> Optional[str]:
    token = os.environ.get("X_BEARER_TOKEN")
    if token:
        return token
    env_paths = [
        Path("/app/Kalshi by Cemini/.env"),
        Path("Kalshi by Cemini/.env"),
        Path.home() / "Cemini-Financial-Suite"
        / "Kalshi by Cemini" / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    for prefix in [
                        "X_BEARER_TOKEN=",
                        "TWITTER_BEARER_TOKEN=",
                    ]:
                        if line.startswith(prefix):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                log.info(f"Token from {env_path}")
                                return val
    return os.environ.get("TWITTER_BEARER_TOKEN")


# ── CLI ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Cemini X Intelligence Harvester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  search   Search tweets by query
  thread   Harvest a conversation thread
  account  Pull tweets from an account
  sprint   Full 3-phase auto-discovery
  budget   Show budget status
  analyze  Export harvest as Claude-ready markdown
  ls       List all harvest files
        """
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--max-tweets", type=int, default=50)

    p = sub.add_parser("thread")
    p.add_argument("tweet_id")

    p = sub.add_parser("account")
    p.add_argument("username")
    p.add_argument("--max-tweets", type=int, default=200)

    p = sub.add_parser("sprint")
    p.add_argument(
        "--category",
        choices=list(DISCOVERY_QUERIES.keys()),
    )

    sub.add_parser("budget")

    p = sub.add_parser("analyze")
    p.add_argument("file")

    sub.add_parser("ls")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    budget = BudgetTracker()

    if args.command == "budget":
        print(budget.summary())
        return

    if args.command == "ls":
        files = sorted(ARCHIVE_DIR.glob("harvest_*.jsonl"))
        if not files:
            print("No harvest files found.")
            return
        print(f"\n{'File':<55} {'Tweets':>7} {'Size':>10}")
        print("-" * 75)
        for f in files:
            count = sum(1 for _ in open(f))
            sz = f.stat().st_size
            sz_str = (
                f"{sz/1024:.1f}KB" if sz < 1048576
                else f"{sz/1048576:.1f}MB"
            )
            print(f"{f.name:<55} {count:>7} {sz_str:>10}")
        print(f"\nTotal: {len(files)} files")
        print(budget.summary())
        return

    if args.command == "analyze":
        fp = Path(args.file)
        md = generate_claude_markdown(fp)
        md_name = fp.stem if fp.suffix else fp.name
        md_path = CLAUDE_DIR / f"{md_name}.md"
        with open(md_path, "w") as f:
            f.write(md)
        print(md)
        log.info(f"\nSaved: {md_path}")
        return

    # Commands that need the API
    token = get_bearer_token()
    if not token:
        print("ERROR: No X_BEARER_TOKEN found.")
        print("Set env var or add to 'Kalshi by Cemini/.env'")
        sys.exit(1)
    if not budget.can_spend():
        print("Budget exhausted.")
        print(budget.summary())
        sys.exit(1)

    client = XClient(token, budget)

    if args.command == "search":
        tweets = harvest_search(client, args.query, args.max_tweets)
        if tweets:
            fp = save_harvest(
                tweets, f"search_{args.query[:30]}",
                {"query": args.query}
            )
            print(f"\nSaved {len(tweets)} tweets -> {fp.name}")
        print(budget.summary())

    elif args.command == "thread":
        tweets = harvest_thread(client, args.tweet_id)
        if tweets:
            fp = save_harvest(tweets, "thread",
                              {"root_id": args.tweet_id})
            print(f"\nSaved {len(tweets)} tweets -> {fp.name}")
        print(budget.summary())

    elif args.command == "account":
        tweets = harvest_account(
            client, args.username, args.max_tweets
        )
        if tweets:
            un = args.username.lstrip("@")
            fp = save_harvest(tweets, f"account_{un}",
                              {"username": un})
            print(f"\nSaved {len(tweets)} from @{un} -> {fp.name}")
        print(budget.summary())

    elif args.command == "sprint":
        cats = (
            [args.category] if args.category
            else list(DISCOVERY_QUERIES.keys())
        )
        run_sprint(client, budget, cats)


if __name__ == "__main__":
    main()
