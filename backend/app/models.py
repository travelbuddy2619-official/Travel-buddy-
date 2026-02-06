from datetime import date
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, ConfigDict


class ItineraryRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "source": "New York",
                "destination": "Tokyo",
                "startDate": "2026-03-01",
                "endDate": "2026-03-07",
                "people": 2,
                "budget": 3000,
                "transport": "Flight",
                "interests": ["temples", "food"],
                "travelStyle": "moderate"
            }
        },
    )

    source: str
    destination: str
    startDate: date = Field(..., alias="startDate")
    endDate: date = Field(..., alias="endDate")
    people: int
    budget: float
    transport: str
    interests: Optional[List[str]] = None
    travelStyle: Optional[str] = Field(default="moderate", alias="travelStyle")


class ReviewSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    rating: Optional[float] = None
    total_reviews: Optional[int] = Field(default=None, alias="totalReviews")
    highlights: List[str] = []


class PopularTimeSlot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    day: str
    busyness_text: str = Field(..., alias="busynessText")


class WeatherSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: date
    summary: str
    icon: Optional[str] = None
    temp_min_c: float = Field(..., alias="tempMinC")
    temp_max_c: float = Field(..., alias="tempMaxC")


class PlaceDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    location: str
    summary: str
    photos: List[str]
    reviews: ReviewSummary
    popular_times: List[PopularTimeSlot] = Field(default_factory=list, alias="popularTimes")


class WeatherBundle(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    location: str
    forecast: List[WeatherSnapshot]


class PracticalInfo(BaseModel):
    """Practical/realistic information about a place"""
    model_config = ConfigDict(populate_by_name=True)
    typical_duration: Optional[str] = Field(default=None, alias="typicalDuration")
    best_time_to_visit: Optional[str] = Field(default=None, alias="bestTimeToVisit")
    ticket_info: Optional[str] = Field(default=None, alias="ticketInfo")
    opening_hours: Optional[str] = Field(default=None, alias="openingHours")
    important_tips: List[str] = Field(default_factory=list, alias="importantTips")
    warnings: List[str] = Field(default_factory=list, alias="warnings")
    crowd_predictions: Optional[dict] = Field(default=None, alias="crowdPredictions")


class PlaceInfo(BaseModel):
    """Detailed info about a place/attraction"""
    model_config = ConfigDict(populate_by_name=True)
    name: str
    description: Optional[str] = None
    type: Optional[str] = None  # temple, beach, museum, etc.
    rating: Optional[float] = None
    total_reviews: Optional[int] = Field(default=None, alias="totalReviews")
    review_summary: Optional[str] = Field(default=None, alias="reviewSummary")
    images: List[str] = []
    address: Optional[str] = None
    estimated_time: Optional[str] = Field(default=None, alias="estimatedTime")
    opening_hours: Optional[str] = Field(default=None, alias="openingHours")
    practical_info: Optional[PracticalInfo] = Field(default=None, alias="practicalInfo")
    crowd_predictions: Optional[dict] = Field(default=None, alias="crowdPredictions")


class ScheduleRestaurant(BaseModel):
    """Restaurant info for meal schedule items"""
    model_config = ConfigDict(populate_by_name=True)
    name: str
    cuisine: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = Field(default=None, alias="totalReviews")
    price_level: Optional[str] = Field(default=None, alias="priceLevel")
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    review_snippet: Optional[str] = Field(default=None, alias="reviewSnippet")
    images: List[str] = Field(default_factory=list)
    must_try: List[str] = Field(default_factory=list, alias="mustTry")
    opening_hours: Optional[str] = Field(default=None, alias="openingHours")


class TimeSlotActivity(BaseModel):
    """Activity with specific time"""
    model_config = ConfigDict(populate_by_name=True)
    time: str  # e.g., "06:00 AM", "10:30 AM"
    activity: str
    description: Optional[str] = None
    duration: Optional[str] = None  # e.g., "2 hours"
    place: Optional[PlaceInfo] = None
    tips: Optional[str] = None
    crowd_predictions: Optional[dict] = Field(default=None, alias="crowdPredictions")
    # Meal-related fields
    is_meal: Optional[bool] = Field(default=None, alias="isMeal")
    meal_type: Optional[str] = Field(default=None, alias="mealType")  # breakfast, lunch, dinner, snack
    restaurant: Optional[ScheduleRestaurant] = None


class LocationInsight(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    location: str
    description: str
    photos: List[str] = []
    reviews: Optional[ReviewSummary] = None
    popular_times: List[PopularTimeSlot] = Field(default_factory=list, alias="popularTimes")
    weather: List[WeatherSnapshot] = []


class Restaurant(BaseModel):
    """Real restaurant recommendation with details from Google"""
    model_config = ConfigDict(populate_by_name=True)
    name: str
    cuisine: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = Field(default=None, alias="totalReviews")
    price_level: Optional[str] = Field(default=None, alias="priceLevel")
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    review_snippet: Optional[str] = Field(default=None, alias="reviewSnippet")
    images: List[str] = Field(default_factory=list)
    must_try: List[str] = Field(default_factory=list, alias="mustTry")
    opening_hours: Optional[str] = Field(default=None, alias="openingHours")
    google_maps_url: Optional[str] = Field(default=None, alias="googleMapsUrl")


class DiningRecommendations(BaseModel):
    """Structured dining recommendations"""
    model_config = ConfigDict(populate_by_name=True)
    restaurants: List[Restaurant] = []


class DayPlan(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    day: int
    date: Optional[str] = None
    title: Optional[str] = None
    theme: Optional[str] = None  # Added for new structure
    summary: Optional[str] = None
    schedule: List[TimeSlotActivity] = []  # Time-wise activities
    location_insight: Optional[LocationInsight] = Field(default=None, alias="locationInsight")
    dining: List[str] = []  # Kept for backward compatibility
    dining_recommendations: Optional[DiningRecommendations] = Field(default=None, alias="diningRecommendations")
    estimated_cost: Optional[str] = Field(default=None, alias="estimatedCost")


class TripDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    origin: str
    destination: str
    travelers: int
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    budget_per_person: float = Field(alias="budgetPerPerson")
    transport_preference: str = Field(alias="transportPreference")


class WeatherInfo(BaseModel):
    """Weather information from Weather Agent"""
    model_config = ConfigDict(populate_by_name=True)
    summary: Optional[str] = None
    forecasts: List[dict] = []
    recommendations: List[str] = []


class CityHighlights(BaseModel):
    """City highlights from City Explorer Agent"""
    model_config = ConfigDict(populate_by_name=True)
    famous_food: List[dict] = Field(default_factory=list, alias="famousFood")
    famous_restaurants: List[dict] = Field(default_factory=list, alias="famousRestaurants")
    local_specialties: List[dict] = Field(default_factory=list, alias="localSpecialties")
    shopping_areas: List[dict] = Field(default_factory=list, alias="shoppingAreas")
    festivals: List[dict] = Field(default_factory=list, alias="festivals")
    local_tips: List[str] = Field(default_factory=list, alias="localTips")
    transport_tips: List[str] = Field(default_factory=list, alias="transportTips")
    hidden_gems: List[dict] = Field(default_factory=list, alias="hiddenGems")


class BudgetBreakdown(BaseModel):
    """Budget breakdown"""
    model_config = ConfigDict(populate_by_name=True)
    accommodation: Optional[float] = None
    food: Optional[float] = None
    transport: Optional[float] = None
    activities: Optional[float] = None


class ItineraryResponse(BaseModel):
    """Multi-Agent System Itinerary Response"""
    model_config = ConfigDict(populate_by_name=True)
    
    # Core fields
    destination: str
    startDate: date = Field(alias="startDate")
    endDate: date = Field(alias="endDate")
    days: List[DayPlan]
    
    # From Weather Agent
    weather: Optional[WeatherInfo] = None
    
    # From City Explorer Agent
    cityHighlights: Optional[CityHighlights] = Field(default=None, alias="cityHighlights")
    
    # Smart Trip Insights
    tripInsights: Optional[dict] = Field(default=None, alias="tripInsights")
    
    # General trip info
    packingList: List[str] = Field(default_factory=list, alias="packingList")
    budgetBreakdown: Optional[dict] = Field(default=None, alias="budgetBreakdown")
    emergencyContacts: List[Any] = Field(default_factory=list, alias="emergencyContacts")  # Can be strings or dicts
    
    # Legacy fields for backward compatibility
    title: Optional[str] = None
    lead_planner: Optional[str] = Field(default=None, alias="leadPlanner")
    summary: Optional[str] = None
    details: Optional[TripDetails] = None
    travel_tips: List[str] = Field(default_factory=list, alias="travelTips")
    packing_suggestions: List[str] = Field(default_factory=list, alias="packingSuggestions")
