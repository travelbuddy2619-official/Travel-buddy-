"""
Multi-Agent Travel Planning System

Agents:
- WeatherAgent: Researches weather forecasts and provides packing/activity recommendations
- PlaceResearchAgent: Gathers detailed place info (duration, hours, tips, warnings)
- PhotoReviewAgent: Fetches real Google photos and review summaries
- DiningAgent: Finds restaurants for meals with ratings and must-try dishes
- CityExplorerAgent: Researches famous food, local tips, shopping, events
- ReplanningAgent: Handles user modifications via chat
- AgentOrchestrator: Coordinates all agents for comprehensive trip planning
"""

from app.agents.weather_agent import WeatherAgent
from app.agents.place_research_agent import PlaceResearchAgent
from app.agents.photo_review_agent import PhotoReviewAgent
from app.agents.dining_agent import DiningAgent
from app.agents.city_explorer_agent import CityExplorerAgent
from app.agents.replanning_agent import ReplanningAgent
from app.agents.orchestrator import AgentOrchestrator

__all__ = [
    "WeatherAgent",
    "PlaceResearchAgent",
    "PhotoReviewAgent",
    "DiningAgent",
    "CityExplorerAgent",
    "ReplanningAgent",
    "AgentOrchestrator",
]
