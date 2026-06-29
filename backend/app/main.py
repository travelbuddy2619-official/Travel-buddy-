from __future__ import annotations

import hashlib
import json
import logging
import secrets
import sqlite3
import traceback
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
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
DB_PATH = "travel_planner.db"

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


def _normalize_transport_type(transport: str) -> str:
    value = (transport or "").strip().lower()
    if value in {"flight", "flights", "plane", "air"}:
        return "flight"
    if value in {"train", "trains", "rail"}:
        return "train"
    if value in {"bus", "buses", "coach"}:
        return "bus"
    if value in {"car", "cab", "taxi", "drive", "self drive", "self-drive"}:
        return "car"
    return "flight"


def _transport_options_for_mode(search_result: dict, mode: str) -> list[dict]:
    if mode == "flight":
        return search_result.get("flights", [])
    if mode == "train":
        return search_result.get("trains", [])
    if mode == "bus":
        return search_result.get("buses", [])
    if mode == "car":
        return search_result.get("cars", [])
    return []


def _transport_display_name(option: dict, mode: str) -> str:
    if mode == "flight":
        return f"{option.get('airline', 'Flight')} {option.get('flight_number', '')}".strip()
    if mode == "train":
        return f"{option.get('train_name', 'Train')} #{option.get('train_number', '')}".strip()
    if mode == "bus":
        return f"{option.get('operator', 'Bus')} {option.get('bus_type', '')}".strip()
    if mode == "car":
        return option.get("name") or option.get("vehicle_type") or "Car transfer"
    return option.get("name", "Transport")


def _build_transportation_plan(source: str, destination: str, mode: str, search_result: dict) -> dict:
    options = _transport_options_for_mode(search_result, mode)
    selected = options[0] if options else None
    return {
        "mode": mode.title(),
        "origin": source,
        "destination": destination,
        "travelDate": search_result.get("travel_date"),
        "selectedOption": selected,
        "options": options,
        "searchSummary": search_result.get("search_summary", ""),
        "dataSource": selected.get("data_source") if selected else search_result.get("data_source"),
        "isRealData": bool(selected.get("is_real_data")) if selected else False,
    }


def _add_transport_to_itinerary(itinerary: dict, request: ItineraryRequest, transportation_plan: dict) -> dict:
    itinerary["details"] = {
        "origin": request.source,
        "destination": request.destination,
        "travelers": request.people,
        "startDate": str(request.startDate),
        "endDate": str(request.endDate),
        "budgetPerPerson": request.budget,
        "transportPreference": request.transport,
    }
    itinerary["transportationPlan"] = transportation_plan
    itinerary["suggestedTransport"] = transportation_plan.get("options", [])

    selected = transportation_plan.get("selectedOption") or {}
    if selected:
        total_transport = selected.get("total_price") or (
            selected.get("price_per_person", 0) * max(request.people, 1)
        )
        budget_breakdown = itinerary.setdefault("budgetBreakdown", {})
        budget_breakdown["transport"] = total_transport

        day_one = next((day for day in itinerary.get("days", []) if day.get("day") == 1), None)
        if day_one is not None:
            schedule = day_one.setdefault("schedule", [])
            already_has_transport = any(
                "travel from" in (slot.get("activity", "") or "").lower()
                or "arrival transfer" in (slot.get("activity", "") or "").lower()
                for slot in schedule
            )
            if not already_has_transport:
                mode = transportation_plan.get("mode", request.transport)
                departure = selected.get("departure_time") or selected.get("start_time") or "Start of day"
                arrival = selected.get("arrival_time") or selected.get("end_time") or "Arrival time varies"
                name = _transport_display_name(selected, mode.lower())
                schedule.insert(0, {
                    "time": departure,
                    "activity": f"Travel from {request.source} to {request.destination} by {mode}",
                    "description": (
                        f"{name}. Departure: {departure}; arrival: {arrival}; "
                        f"duration: {selected.get('duration', 'varies')}; "
                        f"estimated cost: ₹{selected.get('price_per_person', 0):,} per person."
                    ),
                    "duration": selected.get("duration"),
                    "tips": f"Data source: {selected.get('data_source', 'travel search')}. Verify availability before booking.",
                    "isMeal": False,
                })

    return itinerary


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    conn = _get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_itineraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                destination TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                itinerary_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()


def _issue_token() -> str:
    return secrets.token_urlsafe(40)


def _extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def _require_user(authorization: Optional[str]) -> sqlite3.Row:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")

    conn = _get_db()
    try:
        row = conn.execute(
            """
            SELECT u.id, u.name, u.email, s.token
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid session")
        return row
    finally:
        conn.close()


@app.on_event("startup")
async def on_startup() -> None:
    _init_db()


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


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class SaveItineraryRequest(BaseModel):
    title: Optional[str] = None
    status: str = "active"
    itinerary: dict


class UpdateItineraryStatusRequest(BaseModel):
    status: str


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
        transport_type = _normalize_transport_type(request.transport)
        try:
            travel_search_result = await travel_booking_agent.search_travel_options(
                origin=request.source,
                destination=request.destination,
                travel_date=str(request.startDate),
                travel_type=transport_type,
                budget=int(request.budget) if request.budget else None,
                passengers=request.people,
            )
        except Exception as exc:
            logger.warning("Travel search failed; continuing with itinerary planning: %s", exc)
            travel_search_result = {
                "origin": request.source,
                "destination": request.destination,
                "travel_date": str(request.startDate),
                "passengers": request.people,
                "budget": int(request.budget) if request.budget else None,
                "flights": [],
                "trains": [],
                "buses": [],
                "cars": [],
                "search_summary": "Transport search failed; itinerary uses estimated timing.",
                "data_source": "fallback",
            }
        transportation_plan = _build_transportation_plan(
            request.source,
            request.destination,
            transport_type,
            travel_search_result,
        )

        # Use the multi-agent orchestrator
        result = await orchestrator.plan_trip(
            source=request.source,
            destination=request.destination,
            start_date=str(request.startDate),
            end_date=str(request.endDate),
            budget=request.budget,
            travelers=request.people,
            transport_preference=request.transport,
            transportation_plan=transportation_plan,
            interests=request.interests,
            travel_style=request.travelStyle,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Planning failed: {', '.join(result.get('errors', ['Unknown error']))}"
            )
        
        itinerary = _add_transport_to_itinerary(
            result.get("itinerary", {}),
            request,
            transportation_plan,
        )
        
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
            transportationPlan=itinerary.get("transportationPlan"),
            suggestedTransport=itinerary.get("suggestedTransport", []),
            packingList=itinerary.get("packingList", []),
            budgetBreakdown=itinerary.get("budgetBreakdown", {}),
            emergencyContacts=itinerary.get("emergencyContacts", []),
            details=itinerary.get("details"),
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


@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    email = request.email.strip().lower()
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    conn = _get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email is already registered")

        salt = secrets.token_hex(16)
        password_hash = _hash_password(request.password, salt)
        now = datetime.utcnow().isoformat()

        cur = conn.execute(
            "INSERT INTO users(name, email, password_hash, password_salt, created_at) VALUES(?,?,?,?,?)",
            (request.name.strip(), email, password_hash, salt, now),
        )
        user_id = cur.lastrowid

        token = _issue_token()
        conn.execute(
            "INSERT INTO user_sessions(token, user_id, created_at) VALUES(?,?,?)",
            (token, user_id, now),
        )
        conn.commit()

        return AuthResponse(token=token, user={"id": user_id, "name": request.name.strip(), "email": email})
    finally:
        conn.close()


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    email = request.email.strip().lower()

    conn = _get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email, password_hash, password_salt FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        provided_hash = _hash_password(request.password, user["password_salt"])
        if provided_hash != user["password_hash"]:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = _issue_token()
        now = datetime.utcnow().isoformat()
        conn.execute("INSERT INTO user_sessions(token, user_id, created_at) VALUES(?,?,?)", (token, user["id"], now))
        conn.commit()

        return AuthResponse(token=token, user={"id": user["id"], "name": user["name"], "email": user["email"]})
    finally:
        conn.close()


@app.get("/api/auth/me")
async def get_me(authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@app.post("/api/users/itineraries")
async def save_user_itinerary(request: SaveItineraryRequest, authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)

    itinerary = request.itinerary or {}
    destination = itinerary.get("destination")
    start_date = itinerary.get("startDate")
    end_date = itinerary.get("endDate")
    title = request.title or f"Trip to {destination or 'Destination'}"
    now = datetime.utcnow().isoformat()

    conn = _get_db()
    try:
        cur = conn.execute(
            """
            INSERT INTO user_itineraries(user_id, title, destination, start_date, end_date, status, itinerary_json, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                user["id"],
                title,
                destination,
                start_date,
                end_date,
                request.status if request.status in {"active", "previous"} else "active",
                json.dumps(itinerary),
                now,
                now,
            ),
        )
        conn.commit()
        return {"success": True, "id": cur.lastrowid}
    finally:
        conn.close()


@app.get("/api/users/itineraries")
async def list_user_itineraries(authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    conn = _get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, title, destination, start_date, end_date, status, itinerary_json, created_at, updated_at
            FROM user_itineraries
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC
            """,
            (user["id"],),
        ).fetchall()

        items = []
        for row in rows:
            try:
                itinerary_obj = json.loads(row["itinerary_json"])
            except json.JSONDecodeError:
                itinerary_obj = {}
            items.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "destination": row["destination"],
                    "startDate": row["start_date"],
                    "endDate": row["end_date"],
                    "status": row["status"],
                    "createdAt": row["created_at"],
                    "updatedAt": row["updated_at"],
                    "itinerary": itinerary_obj,
                }
            )
        return {"items": items}
    finally:
        conn.close()


@app.patch("/api/users/itineraries/{itinerary_id}/status")
async def update_itinerary_status(
    itinerary_id: int,
    request: UpdateItineraryStatusRequest,
    authorization: Optional[str] = Header(default=None),
):
    user = _require_user(authorization)
    if request.status not in {"active", "previous"}:
        raise HTTPException(status_code=400, detail="Status must be either active or previous")

    conn = _get_db()
    try:
        result = conn.execute(
            """
            UPDATE user_itineraries
            SET status = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (request.status, datetime.utcnow().isoformat(), itinerary_id, user["id"]),
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        return {"success": True}
    finally:
        conn.close()


@app.delete("/api/users/itineraries/{itinerary_id}")
async def delete_itinerary(itinerary_id: int, authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)

    conn = _get_db()
    try:
        result = conn.execute(
            "DELETE FROM user_itineraries WHERE id = ? AND user_id = ?",
            (itinerary_id, user["id"]),
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        return {"success": True}
    finally:
        conn.close()


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
    cars: List[dict] = []
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
            cars=result.get("cars", []),
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
