import httpx
import asyncio
import feedparser
from datetime import datetime
from app.core.config import settings

class MuskDataSources:
    def __init__(self):
        self.spacex_url = "https://api.spacexdata.com/v4/launches/upcoming"
        self.news_feeds = {
            "Tesla": "https://finance.yahoo.com/rss/headline?s=TSLA",
            "Crypto": "https://cointelegraph.com/rss/tag/bitcoin",
            "Tech": "https://feeds.feedburner.com/TechCrunch/"
        }

    async def _fetch_feed(self, client, url, company):
        try:
            resp = await client.get(url, timeout=10.0)
            if resp.status_code != 200:
                return {"volatility": 0, "headlines": []}
            
            feed = feedparser.parse(resp.text)
            headlines = []
            volatility = 0
            if hasattr(feed, 'entries'):
                for entry in feed.entries[:5]:
                    title = entry.title.lower()
                    if any(x in title for x in ["musk", "tesla", "spacex", "xai", "grok", "neuralink"]):
                        volatility += 1
                        headlines.append(f"[{company}] {entry.title[:50]}...")
            return {"volatility": volatility, "headlines": headlines}
        except Exception as e:
            print(f"[!] Feed Error ({company}): {e}")
            return {"volatility": 0, "headlines": []}

    async def get_empire_status(self):
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_feed(client, url, name) for name, url in self.news_feeds.items()]
            results = await asyncio.gather(*tasks)
            
        total_volatility = sum(r['volatility'] for r in results)
        all_headlines = []
        for r in results:
            all_headlines.extend(r['headlines'])
            
        return {
            "volatility_score": total_volatility,
            "active_headlines": all_headlines
        }

    async def get_spacex_launches(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.spacex_url, timeout=5.0)
                res = resp.json()
            
            nearby = []
            now = datetime.utcnow()
            for launch in res:
                l_date = datetime.fromisoformat(launch['date_utc'].replace('Z', ''))
                diff = (l_date - now).total_seconds()
                
                if -43200 < diff < 86400:
                    intensity = "EXTREME" if "Starship" in launch.get('name', '') else "HIGH"
                    nearby.append({
                        "mission": launch['name'],
                        "intensity": intensity,
                        "t_minus_hours": round(diff / 3600, 1)
                    })
            return nearby
        except Exception as e:
            print(f"[!] SpaceX API Error: {e}")
            return []
