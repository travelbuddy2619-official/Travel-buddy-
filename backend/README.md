# Agentic Travel Planner Backend

This backend replaces the previous Node/Express server with a FastAPI + LangChain stack. A Lead Planner agent talks to Gemini, orchestrates multiple tools (MapTiler Places + OpenWeather), and emits structured itineraries via Pydantic models that always include locations, photos, reviews, and weather insights.

## Requirements

- Python 3.10+
- API keys: `GOOGLE_API_KEY`, `MAPTILER_API_KEY`, `OPENWEATHER_API_KEY`

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your keys
uvicorn app.main:app --reload --port 5000
```

The service exposes `POST /api/itinerary` (same shape expected by the React app) and a lightweight `/health` probe.
