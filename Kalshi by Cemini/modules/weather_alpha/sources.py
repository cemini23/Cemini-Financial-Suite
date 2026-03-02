import httpx
import statistics
import time
from app.core.config import settings

class WeatherSource:
    def __init__(self):
        self.nws_headers = {"User-Agent": settings.NWS_USER_AGENT}
        
        # Cache Storage: {city_code: {'data': ..., 'expires': timestamp}}
        self._cache = {}
        self.CACHE_DURATION = 600  # 10 Minutes (Weather doesn't change instantly)

        self.cities = {
            "MIA": {"name": "Miami", "lat": 25.7934, "lon": -80.2901, "office": "MFL", "gridX": 105, "gridY": 50},
            "CHI": {"name": "Chicago", "lat": 41.9742, "lon": -87.9073, "office": "LOT", "gridX": 75, "gridY": 72},
            "NYC": {"name": "New York", "lat": 40.7831, "lon": -73.9712, "office": "OKX", "gridX": 33, "gridY": 35},
            "AUS": {"name": "Austin", "lat": 30.1945, "lon": -97.6699, "office": "EWX", "gridX": 155, "gridY": 90},
            "LAX": {"name": "Los Angeles", "lat": 33.9416, "lon": -118.4085, "office": "LOX", "gridX": 154, "gridY": 44},
            "DEN": {"name": "Denver", "lat": 39.8561, "lon": -104.6737, "office": "BOU", "gridX": 62, "gridY": 61},
            "PHX": {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740, "office": "PSR", "gridX": 158, "gridY": 57},
            "LAS": {"name": "Las Vegas", "lat": 36.0840, "lon": -115.1537, "office": "VEF", "gridX": 129, "gridY": 90}
        }

    async def _fetch_url(self, client, url, params=None, headers=None):
        """
        Generic Async Fetcher with Error Handling
        """
        try:
            resp = await client.get(url, params=params, headers=headers, timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[!] Network Error ({url}): {e}")
            return None

    async def get_nws_forecast(self, client, city):
        """
        Async fetch for NWS — returns high and overnight low for degree-day calculations.
        """
        url = f"https://api.weather.gov/gridpoints/{city['office']}/{city['gridX']},{city['gridY']}/forecast"
        data = await self._fetch_url(client, url, headers=self.nws_headers)

        if not data: return None
        try:
            periods = data['properties']['periods']
            day   = next((p for p in periods if p['isDaytime']), None)
            night = next((p for p in periods if not p['isDaytime']), None)
            return {
                "high": day['temperature']   if day   else None,
                "low":  night['temperature'] if night else None,
            }
        except (KeyError, TypeError):
            return None

    async def get_open_meteo_consensus(self, client, city):
        """
        Async fetch for ECMWF + GFS — max and min for degree-day calculations.
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": city['lat'],
            "longitude": city['lon'],
            "daily": "temperature_2m_max,temperature_2m_min",
            "temperature_unit": "fahrenheit",
            "timezone": "auto",
            "models": "ecmwf_ifs,gfs_seamless"
        }
        res = await self._fetch_url(client, url, params=params)

        if not res: return None
        try:
            d = res['daily']
            return {
                "ECMWF":     d['temperature_2m_max_ecmwf_ifs'][0],
                "GFS":       d['temperature_2m_max_gfs_seamless'][0],
                "ECMWF_min": d['temperature_2m_min_ecmwf_ifs'][0],
                "GFS_min":   d['temperature_2m_min_gfs_seamless'][0],
            }
        except (KeyError, TypeError, IndexError):
            return None

    async def get_openweather_data(self, client, city):
        """
        Async fetch for OpenWeather (Model 4)
        """
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": city['lat'],
            "lon": city['lon'],
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "imperial"
        }
        res = await self._fetch_url(client, url, params=params)
        return res['main']['temp'] if res and 'main' in res else None

    async def get_visual_crossing_data(self, client, city):
        """
        Async fetch for Visual Crossing (Model 5)
        Returns today's forecast high and low in Fahrenheit.
        """
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city['lat']},{city['lon']}/today"
        params = {
            "unitGroup": "us",
            "key": settings.VISUAL_CROSSING_API_KEY,
            "contentType": "json",
            "include": "days",
            "elements": "tempmax,tempmin"
        }
        res = await self._fetch_url(client, url, params=params)
        try:
            day = res['days'][0]
            return {"max": day['tempmax'], "min": day['tempmin']}
        except (KeyError, TypeError, IndexError):
            return None

    async def get_aggregated_forecast(self, city_code: str):
        # 1. CHECK CACHE (Speed Optimization)
        now = time.time()
        if city_code in self._cache:
            cached = self._cache[city_code]
            if now < cached['expires']:
                return cached['data'] # Return instantly from RAM

        city = self.cities.get(city_code)
        if not city: return None

        # 2. ASYNC REQUESTS (Parallel Execution)
        import asyncio
        async with httpx.AsyncClient() as client:
            try:
                nws_task = self.get_nws_forecast(client, city)
                models_task = self.get_open_meteo_consensus(client, city)
                owm_task = self.get_openweather_data(client, city)
                vc_task = self.get_visual_crossing_data(client, city)

                # Wait for all models to finish in parallel, capturing exceptions
                nws, models, owm, vc = await asyncio.gather(nws_task, models_task, owm_task, vc_task, return_exceptions=True)
            except Exception as e:
                print(f"[!] Weather Fetch Critical Fail: {e}")
                nws, models, owm, vc = None, None, None, None

        # 3. ROBUST ERROR HANDLING
        if isinstance(nws, Exception) or nws is None:
            nws = {"high": 0.0, "low": 0.0}
        if isinstance(models, Exception) or models is None:
            models = {"ECMWF": 0.0, "GFS": 0.0, "ECMWF_min": 0.0, "GFS_min": 0.0}
        if isinstance(owm, Exception) or owm is None:
            owm = 0.0
        if isinstance(vc, Exception) or vc is None:
            vc = {"max": 0.0, "min": 0.0}

        nws_high = nws.get("high") or 0.0
        nws_low  = nws.get("low")  or 0.0
        vc_max   = vc.get("max")   or 0.0
        vc_min   = vc.get("min")   or 0.0

        # Consensus high: NWS 2x (~33%), ECMWF/GFS/OWM/VC 1x (~17% each)
        sources_list = [nws_high, models.get("ECMWF", 0), models.get("GFS", 0), owm, vc_max]
        valid_sources = [s for s in sources_list if s > 1.0]

        if not valid_sources:
            avg_temp = 0.0
            variance = 0.0
        else:
            weighted_sources = []
            if nws_high > 1.0: weighted_sources.extend([nws_high, nws_high])
            if models.get("ECMWF", 0) > 1.0: weighted_sources.append(models["ECMWF"])
            if models.get("GFS", 0) > 1.0: weighted_sources.append(models["GFS"])
            if owm > 1.0: weighted_sources.append(owm)
            if vc_max > 1.0: weighted_sources.append(vc_max)

            avg_temp = statistics.mean(weighted_sources)
            variance = statistics.stdev(weighted_sources) if len(weighted_sources) > 1 else 0.0

        # Consensus low — used for degree-day T_avg; fall back to T_high - 15 if no lows available
        min_sources = []
        if nws_low > 1.0: min_sources.extend([nws_low, nws_low])
        if models.get("ECMWF_min", 0) > 1.0: min_sources.append(models["ECMWF_min"])
        if models.get("GFS_min", 0) > 1.0: min_sources.append(models["GFS_min"])
        if vc_min > 1.0: min_sources.append(vc_min)

        avg_min = statistics.mean(min_sources) if min_sources else max(0.0, avg_temp - 15.0)
        t_avg = (avg_temp + avg_min) / 2.0

        # Agricultural degree-day metrics (all base °F)
        gdd_50 = max(0.0, t_avg - 50.0)   # Standard crops: corn, soy, cotton
        gdd_41 = max(0.0, t_avg - 41.0)   # Cool-season crops: wheat, barley, canola
        hdd = max(0.0, 65.0 - t_avg)       # Heating demand proxy
        cdd = max(0.0, t_avg - 65.0)       # Cooling demand proxy

        result = {
            "city": city_code,
            "consensus_temp": round(avg_temp, 1),
            "variance": round(variance, 2),
            "sources": {
                "NWS": nws_high if nws_high > 1.0 else 0,
                "ECMWF": models.get("ECMWF", 0) if models.get("ECMWF", 0) > 1.0 else 0,
                "GFS": models.get("GFS", 0) if models.get("GFS", 0) > 1.0 else 0,
                "OpenWeather": owm if owm > 1.0 else 0,
                "VisualCrossing": vc_max if vc_max > 1.0 else 0
            },
            "agricultural_metrics": {
                "t_avg": round(t_avg, 1),
                "t_min_consensus": round(avg_min, 1),
                "gdd": {
                    "base_50": round(gdd_50, 1),
                    "base_41": round(gdd_41, 1),
                },
                "hdd": round(hdd, 1),
                "cdd": round(cdd, 1),
            }
        }

        # 4. UPDATE CACHE
        self._cache[city_code] = {
            "data": result,
            "expires": now + self.CACHE_DURATION
        }
        
        return result
