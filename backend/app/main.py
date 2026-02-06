from __future__ import annotations

import logging
import traceback
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.orchestrator import AgentOrchestrator
from app.agents.travel_booking_agent import TravelBookingAgent
from app.agents.hotel_booking_agent import HotelBookingAgent
from app.config import get_settings
from app.models import ItineraryRequest, ItineraryResponse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Agentic Travel Planner - Multi-Agent System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Multi-Agent Orchestrator
orchestrator = AgentOrchestrator(
    groq_api_key=settings.groq_api_key,
    serper_api_key=settings.serper_api_key,
    weather_api_key=settings.openweather_api_key,
    rapidapi_key=settings.rapidapi_key,
)

# Initialize Booking Agents with multiple API keys for real data
travel_booking_agent = TravelBookingAgent(
    groq_api_key=settings.groq_api_key,
    serper_api_key=settings.serper_api_key,
    rapidapi_key=settings.rapidapi_key,
    amadeus_api_key=settings.amadeus_api_key,
    amadeus_api_secret=settings.amadeus_api_secret
)
hotel_booking_agent = HotelBookingAgent(
    groq_api_key=settings.groq_api_key,
    serper_api_key=settings.serper_api_key,
    rapidapi_key=settings.rapidapi_key
)

# Store current itinerary for chat/replanning
current_itinerary_store = {}


# ===== Request/Response Models for Chat =====
class ChatMessage(BaseModel):
    message: str
    session_id: str
    chat_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    reply: str
    is_modification_request: bool = False
    should_replan: bool = False
    success: bool = True
    action: Optional[str] = None  # Frontend action command
    action_data: Optional[dict] = None  # Data for the action
    agent_used: Optional[str] = None  # Which agent handled the request


class ModifyRequest(BaseModel):
    session_id: str
    modification: str


class ModifyResponse(BaseModel):
    success: bool
    changes_made: List[str]
    explanation: Optional[str]
    modified_itinerary: Optional[dict]


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "2.0.0",
        "system": "Multi-Agent Travel Planner",
        "agents": [
            "Weather Agent",
            "Place Research Agent", 
            "Photo & Review Agent",
            "Dining Agent",
            "City Explorer Agent",
            "Replanning Agent"
        ]
    }


@app.post("/api/itinerary", response_model=ItineraryResponse)
async def create_itinerary(request: ItineraryRequest):
    """
    Main endpoint to create an itinerary using the Multi-Agent System.
    
    Agents involved:
    1. Weather Agent - Fetches weather data and recommendations
    2. City Explorer Agent - Researches famous food, local tips
    3. Lead Planner (LLM) - Creates the base itinerary structure
    4. Place Research Agent - Gathers practical info for each place
    5. Photo & Review Agent - Fetches real photos and reviews
    6. Dining Agent - Finds restaurants for meal breaks
    """
    logger.info(f"🚀 Received itinerary request: {request.destination}")
    
    if request.endDate < request.startDate:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    try:
        # Use the multi-agent orchestrator
        result = await orchestrator.plan_trip(
            destination=request.destination,
            start_date=str(request.startDate),
            end_date=str(request.endDate),
            budget=request.budget,
            interests=request.interests,
            travel_style=request.travelStyle,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Planning failed: {', '.join(result.get('errors', ['Unknown error']))}"
            )
        
        itinerary = result.get("itinerary", {})
        
        # Store for chat/replanning
        session_id = f"{request.destination}_{request.startDate}"
        current_itinerary_store[session_id] = itinerary
        
        # Convert to response model
        response = ItineraryResponse(
            destination=itinerary.get("destination", request.destination),
            startDate=request.startDate,
            endDate=request.endDate,
            days=itinerary.get("days", []),
            weather=itinerary.get("weather"),
            cityHighlights=itinerary.get("cityHighlights"),
            tripInsights=itinerary.get("tripInsights"),
            packingList=itinerary.get("packingList", []),
            budgetBreakdown=itinerary.get("budgetBreakdown", {}),
            emergencyContacts=itinerary.get("emergencyContacts", []),
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error creating itinerary: {exc}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_planner(request: ChatMessage):
    """
    Chat endpoint for asking questions or requesting modifications.
    Uses the Replanning Agent.
    """
    logger.info(f"💬 Chat message: {request.message[:50]}...")
    
    try:
        # Get current itinerary from store
        itinerary = current_itinerary_store.get(request.session_id, {})
        
        if not itinerary:
            return ChatResponse(
                reply="I don't have your current itinerary. Please generate an itinerary first! Use the form above to create one. 📝",
                is_modification_request=False,
                should_replan=False,
                success=True,
                action="scroll_to_section",
                action_data={"section": "itinerary-form"}
            )
        
        # Use orchestrator's smart chat method
        result = await orchestrator.chat(
            message=request.message,
            current_itinerary=itinerary,
            chat_history=request.chat_history
        )
        
        # If itinerary was modified, update the store
        if result.get("action") == "update_itinerary" and result.get("action_data", {}).get("itinerary"):
            current_itinerary_store[request.session_id] = result["action_data"]["itinerary"]
        
        return ChatResponse(
            reply=result.get("reply", "I couldn't process your message."),
            is_modification_request=result.get("is_modification_request", False),
            should_replan=result.get("should_replan", False),
            success=result.get("success", True),
            action=result.get("action"),
            action_data=result.get("action_data"),
            agent_used=result.get("agent_used")
        )
        
    except Exception as exc:
        logger.error(f"Chat error: {exc}")
        return ChatResponse(
            reply="Sorry, I encountered an error. Please try again.",
            is_modification_request=False,
            should_replan=False,
            success=False
        )


@app.post("/api/modify", response_model=ModifyResponse)
async def modify_itinerary(request: ModifyRequest):
    """
    Endpoint to modify the current itinerary.
    Uses the Replanning Agent to process modifications.
    """
    logger.info(f"✏️ Modification request: {request.modification[:50]}...")
    
    try:
        # Get current itinerary
        itinerary = current_itinerary_store.get(request.session_id, {})
        
        if not itinerary:
            return ModifyResponse(
                success=False,
                changes_made=[],
                explanation="No itinerary found. Please generate one first.",
                modified_itinerary=None
            )
        
        # Use orchestrator's modify method
        result = await orchestrator.modify_itinerary(
            current_itinerary=itinerary,
            modification_request=request.modification
        )
        
        if result.get("success") and result.get("modified_itinerary"):
            # Update stored itinerary
            current_itinerary_store[request.session_id] = result["modified_itinerary"]
        
        return ModifyResponse(
            success=result.get("success", False),
            changes_made=result.get("changes_made", []),
            explanation=result.get("explanation"),
            modified_itinerary=result.get("modified_itinerary")
        )
        
    except Exception as exc:
        logger.error(f"Modify error: {exc}")
        return ModifyResponse(
            success=False,
            changes_made=[],
            explanation=f"Error: {str(exc)}",
            modified_itinerary=None
        )


# ===== Travel Booking Models =====
class TravelSearchRequest(BaseModel):
    origin: str
    destination: str
    travel_date: str  # YYYY-MM-DD
    travel_type: str = "all"  # "flight", "train", "bus", "all"
    budget: Optional[int] = None  # Per person budget in INR
    passengers: int = 1


class TravelSearchResponse(BaseModel):
    success: bool
    origin: str
    destination: str
    travel_date: str
    passengers: int
    budget: Optional[int]
    flights: List[dict]
    trains: List[dict]
    buses: List[dict]
    search_summary: str


# ===== Hotel Booking Models =====
class HotelSearchRequest(BaseModel):
    destination: str
    check_in: str  # YYYY-MM-DD
    check_out: str  # YYYY-MM-DD
    guests: int = 2
    rooms: int = 1
    budget_per_night: Optional[int] = None  # Budget per night in INR
    hotel_type: str = "all"  # "budget", "mid-range", "luxury", "all"


class HotelSearchResponse(BaseModel):
    success: bool
    destination: str
    check_in: str
    check_out: str
    nights: int
    guests: int
    rooms: int
    budget_per_night: Optional[int]
    hotels: List[dict]
    search_summary: str


# ===== Travel Booking Endpoint =====
@app.post("/api/search/travel", response_model=TravelSearchResponse)
async def search_travel_options(request: TravelSearchRequest):
    """
    Search for travel options (flights, trains, buses) with best deals.
    
    The Travel Booking Agent:
    1. Searches for available options
    2. Analyzes prices and deals
    3. Returns best 3 options for each transport type
    """
    logger.info(f"✈️ Travel search: {request.origin} → {request.destination} on {request.travel_date}")
    
    try:
        result = await travel_booking_agent.search_travel_options(
            origin=request.origin,
            destination=request.destination,
            travel_date=request.travel_date,
            travel_type=request.travel_type,
            budget=request.budget,
            passengers=request.passengers
        )
        
        return TravelSearchResponse(
            success=True,
            origin=result.get("origin", request.origin),
            destination=result.get("destination", request.destination),
            travel_date=result.get("travel_date", request.travel_date),
            passengers=result.get("passengers", request.passengers),
            budget=result.get("budget"),
            flights=result.get("flights", []),
            trains=result.get("trains", []),
            buses=result.get("buses", []),
            search_summary=result.get("search_summary", "")
        )
        
    except Exception as exc:
        logger.error(f"Travel search error: {exc}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc))


# ===== Hotel Booking Endpoint =====
@app.post("/api/search/hotels", response_model=HotelSearchResponse)
async def search_hotels(request: HotelSearchRequest):
    """
    Search for hotels with review analysis and best value recommendations.
    
    The Hotel Booking Agent:
    1. Searches for hotels in the destination
    2. Fetches and analyzes reviews for each hotel
    3. Evaluates based on ratings, reviews, and pricing
    4. Returns best 3 hotels with detailed analysis
    """
    logger.info(f"🏨 Hotel search: {request.destination} ({request.check_in} to {request.check_out})")
    
    try:
        result = await hotel_booking_agent.search_hotels(
            destination=request.destination,
            check_in=request.check_in,
            check_out=request.check_out,
            guests=request.guests,
            rooms=request.rooms,
            budget_per_night=request.budget_per_night,
            hotel_type=request.hotel_type
        )
        
        return HotelSearchResponse(
            success=True,
            destination=result.get("destination", request.destination),
            check_in=result.get("check_in", request.check_in),
            check_out=result.get("check_out", request.check_out),
            nights=result.get("nights", 1),
            guests=result.get("guests", request.guests),
            rooms=result.get("rooms", request.rooms),
            budget_per_night=result.get("budget_per_night"),
            hotels=result.get("hotels", []),
            search_summary=result.get("search_summary", "")
        )
        
    except Exception as exc:
        logger.error(f"Hotel search error: {exc}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/hotel/{hotel_name}")
async def get_hotel_details(hotel_name: str, destination: str):
    """Get detailed information about a specific hotel."""
    logger.info(f"🏨 Hotel details: {hotel_name} in {destination}")
    
    try:
        details = await hotel_booking_agent.get_hotel_details(hotel_name, destination)
        return {"success": True, "hotel": details}
    except Exception as exc:
        logger.error(f"Hotel details error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
