"""
Weather Agent - Specialized agent for weather research
Fetches detailed weather forecasts for travel dates
"""
from __future__ import annotations

from typing import Optional, Union
from datetime import date, datetime

from app.tools.weather import WeatherForecastTool
from app.models import WeatherBundle


class WeatherAgent:
    """Agent specialized in weather research and forecasting."""
    
    name = "Weather Agent"
    description = "Researches weather conditions for travel dates and provides clothing/activity recommendations"
    
    def __init__(self, api_key: str):
        self._weather_tool = WeatherForecastTool(api_key=api_key)
    
    async def research(self, destination: str, start_date: Union[str, date], end_date: Union[str, date]) -> dict:
        """
        Research weather for the destination during travel dates.
        Returns weather data with recommendations.
        """
        print(f"🌤️ [Weather Agent] Researching weather for {destination}...")
        
        # Convert string dates to date objects if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        try:
            weather_data = await self._weather_tool._arun(location=destination)
            
            if not weather_data:
                return {
                    "success": False,
                    "error": "Could not fetch weather data",
                    "forecast": [],
                    "recommendations": []
                }
            
            # Filter forecasts for travel dates
            travel_forecasts = []
            for forecast in weather_data.forecast:
                if start_date <= forecast.date <= end_date:
                    travel_forecasts.append({
                        "date": str(forecast.date),
                        "summary": forecast.summary,
                        "icon": forecast.icon,
                        "temp_min_c": forecast.temp_min_c,
                        "temp_max_c": forecast.temp_max_c,
                    })
            
            # Generate recommendations based on weather
            recommendations = self._generate_recommendations(travel_forecasts)
            
            print(f"✓ [Weather Agent] Found {len(travel_forecasts)} days of forecast")
            
            return {
                "success": True,
                "location": weather_data.location,
                "forecast": travel_forecasts,
                "recommendations": recommendations,
                "raw_data": weather_data
            }
            
        except Exception as e:
            print(f"✗ [Weather Agent] Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "forecast": [],
                "recommendations": []
            }
    
    def _generate_recommendations(self, forecasts: list) -> list:
        """Generate weather-based recommendations."""
        recommendations = []
        
        has_rain = any("rain" in f.get("summary", "").lower() for f in forecasts)
        has_hot = any(f.get("temp_max_c", 0) > 35 for f in forecasts)
        has_cold = any(f.get("temp_min_c", 30) < 15 for f in forecasts)
        
        if has_rain:
            recommendations.append("🌧️ Rain expected - Carry umbrella and waterproof bags")
            recommendations.append("👟 Wear waterproof footwear for outdoor activities")
        
        if has_hot:
            recommendations.append("☀️ Hot weather expected - Stay hydrated and wear sunscreen")
            recommendations.append("🧢 Carry caps/hats and sunglasses")
            recommendations.append("⏰ Plan outdoor activities for early morning or evening")
        
        if has_cold:
            recommendations.append("🧥 Cold weather expected - Pack warm layers")
            recommendations.append("🧣 Carry jacket, sweater for evenings")
        
        if not recommendations:
            recommendations.append("🌤️ Pleasant weather expected - Great for sightseeing!")
        
        return recommendations
