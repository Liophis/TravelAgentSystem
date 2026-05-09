from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import crud
from app.db.database import get_db, SessionLocal
from app.config import get_runtime_settings, update_runtime_settings
from app.models import (
    TripChatRequest,
    TripChatResponse,
    POISchema,
    POIListResponse,
)

from app.services import (
    answer_trip_question,
    POIService,
    RouteService,
)

router = APIRouter(prefix="/api", tags=["Travel System API"])

# Initialize services
poi_service = POIService()

# Initialize route service with global graph
route_service = RouteService(poi_service.graph)


class RuntimeSettingsPayload(BaseModel):
    """Runtime settings editable from the frontend."""

    api_base_url: Optional[str] = Field(default=None, description="Frontend API base URL")
    amap_web_api_key: Optional[str] = Field(default=None, description="AMap Web Service Key")
    vite_amap_web_js_key: Optional[str] = Field(default=None, description="AMap Web JS Key")
    google_maps_api_key: Optional[str] = Field(default=None, description="Google Maps API Key")
    google_maps_proxy: Optional[str] = Field(default=None, description="Google Maps Proxy")
    xhs_cookie: Optional[str] = Field(default=None, description="XHS Cookie")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI Base URL")
    openai_model: Optional[str] = Field(default=None, description="OpenAI Model")
    log_level: Optional[str] = Field(default=None, description="Log level")


@router.on_event("startup")
async def startup_event(db: Session = Depends(get_db)):
    """Initialize indexes and data structures on startup"""
    # initialize POI index and graph from the database at startup
    db = SessionLocal()
    try:
        poi_service.initialize_poi_index(db)
    finally:
        db.close()


# ==================== Runtime Settings ====================
@router.get("/settings")
def read_runtime_settings():
    return {
        "success": True,
        "message": "ok",
        "data": get_runtime_settings(),
    }


@router.put("/settings")
def save_runtime_settings(payload: RuntimeSettingsPayload):
    updated = update_runtime_settings(payload.model_dump(exclude_unset=True))
    return {
        "success": True,
        "message": "配置已保存并立即生效",
        "data": updated,
    }


# ==================== POI Endpoints ====================
@router.get("/pois", response_model=POIListResponse, tags=["POI"])
def list_pois(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    """Get all POIs with pagination"""
    pois = crud.get_all_pois(db, skip=skip, limit=limit)
    return POIListResponse(
        total=len(pois),
        items=[
            POISchema(
                id=poi.id,
                name=poi.name,
                type=poi.type,
                latitude=poi.latitude,
                longitude=poi.longitude,
                floor=poi.floor,
                description=poi.description,
            )
            for poi in pois
        ],
    )


@router.get("/pois/search", response_model=list[POISchema], tags=["POI"])
def search_pois(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search POIs by keyword using Trie index"""
    poi_service.initialize_poi_index(db)
    return poi_service.search_poi(db, keyword, limit)


@router.get("/pois/{poi_id}", response_model=POISchema, tags=["POI"])
def get_poi(poi_id: int, db: Session = Depends(get_db)):
    """Get POI details by ID"""
    poi_details = poi_service.get_poi_details(db, poi_id)
    if not poi_details:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi_details


@router.post("/pois", response_model=POISchema, tags=["POI"])
def create_poi(poi: POISchema, db: Session = Depends(get_db)):
    """Create a new POI"""
    existing = crud.get_poi_by_name(db, poi.name)
    if existing:
        raise HTTPException(status_code=400, detail="POI name already exists")
    return poi_service.create_poi(db, poi)


# ==================== Route Planning Endpoints ====================
@router.get("/routes/{start_poi_id}/{end_poi_id}", tags=["Route Planning"])
def find_route(start_poi_id: int, end_poi_id: int, db: Session = Depends(get_db)):
    """Find shortest route between two POIs"""
    route = route_service.find_shortest_path(db, start_poi_id, end_poi_id)
    if not route:
        raise HTTPException(status_code=404, detail="Invalid POI IDs")
    return route


# ==================== Trip Generation Endpoint ====================
@router.post("/trips", tags=["Trip"])
def generate_trip(
    city: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    travel_days: int = Query(1, ge=1),
    transportation: str = Query(None),
    accommodation: str = Query(None),
    preferences: str | None = Query(None),
    free_text_input: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Generate a simple trip plan with real POI data from database.

    This endpoint fetches POIs from DB and creates a demo plan with attractions.
    Can be enhanced later to use `POIService`, `RouteService` and external
    LLM/knowledge graph services.
    """
    # Load POIs from database to populate attractions
    pois = crud.get_all_pois(db, skip=0, limit=10)
    attractions = [
        {
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "latitude": poi.latitude,
            "longitude": poi.longitude,
            "description": poi.description,
        }
        for poi in pois
    ]
    
    # Distribute attractions across days
    attractions_per_day = max(1, len(attractions) // travel_days)
    days = []
    
    from datetime import datetime, timedelta
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    for day_idx in range(travel_days):
        day_attractions = attractions[day_idx * attractions_per_day : (day_idx + 1) * attractions_per_day]
        # If last day, include remaining attractions
        if day_idx == travel_days - 1:
            day_attractions = attractions[day_idx * attractions_per_day :]
        
        days.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_index": day_idx,
            "description": f"第 {day_idx + 1} 天: 游览 {len(day_attractions)} 个景点",
            "transportation": transportation or "混合",
            "accommodation": accommodation or "舒适型酒店",
            "attractions": day_attractions,
            "meals": [],
        })
        
        current_date += timedelta(days=1)
    
    # Build response
    demo = {
        "success": True,
        "message": "generated",
        "data": {
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "overall_suggestions": f"这是一个包含 {len(attractions)} 个景点的 {travel_days} 天行程",
            "weather_info": [],
            "budget": {
                "total_attractions": len(attractions) * 100,
                "total_hotels": travel_days * 300,
                "total_meals": travel_days * 100,
                "total_transportation": 200,
                "total": len(attractions) * 100 + travel_days * 300 + travel_days * 100 + 200,
            },
            "days": days,
        },
    }
    return demo


@router.post("/chat/ask", response_model=TripChatResponse, tags=["Trip Chat"])
def ask_trip_chat(payload: TripChatRequest):
    """Answer follow-up questions based on the current trip plan."""
    reply = answer_trip_question(
        message=payload.message,
        trip_plan=payload.trip_plan,
        history=[item.model_dump() for item in payload.history],
    )
    return TripChatResponse(success=True, reply=reply)
