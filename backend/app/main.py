from __future__ import annotations

import logging
import traceback
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.orchestrator import AgentOrchestrator
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
