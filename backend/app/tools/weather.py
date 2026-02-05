from __future__ import annotations

from datetime import datetime
from typing import List

import httpx
from pydantic import BaseModel

from app.models import WeatherSnapshot, WeatherBundle
from app.tools.base import BasePlanningTool

GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherToolInput(BaseModel):
    location: str


class WeatherForecastTool(BasePlanningTool):
    name = "get_weather_forecast"
    description = (
        "Looks up the 7-day weather forecast for the provided location using OpenWeatherMap."
        "Include this whenever travelers need to pack or schedule activities."
    )
    args_schema = WeatherToolInput
    return_model = WeatherBundle

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def _arun(self, **kwargs) -> WeatherBundle:
        location = kwargs["location"]
        async with httpx.AsyncClient(timeout=20) as client:
            geocode_params = {"q": location, "limit": 1, "appid": self.api_key}
            geocode_resp = await client.get(GEOCODE_URL, params=geocode_params)
            geocode_resp.raise_for_status()
            geo_data = geocode_resp.json()
            if not geo_data:
                raise ValueError(f"Unable to geocode location '{location}' for weather forecast")
            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]

            weather_params = {
                "lat": lat,
                "lon": lon,
                "units": "metric",
                "appid": self.api_key,
            }
            weather_resp = await client.get(WEATHER_URL, params=weather_params)
            weather_resp.raise_for_status()
            weather_json = weather_resp.json()
            
            # Group forecast by day (2.5 API returns 3-hour intervals)
            daily_data = {}
            for item in weather_json.get("list", []):
                date = datetime.utcfromtimestamp(item["dt"]).date()
                if date not in daily_data:
                    daily_data[date] = {
                        "temps": [],
                        "weather": item["weather"][0],
                    }
                daily_data[date]["temps"].append(item["main"]["temp"])

            snapshots: List[WeatherSnapshot] = []
            for date, data in list(daily_data.items())[:7]:
                temps = data["temps"]
                snapshots.append(
                    WeatherSnapshot(
                        date=date,
                        summary=data["weather"]["description"].title(),
                        icon=f"https://openweathermap.org/img/wn/{data['weather']['icon']}@2x.png",
                        temp_min_c=min(temps),
                        temp_max_c=max(temps),
                    )
                )

            return WeatherBundle(location=location, forecast=snapshots)
