from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import crud
from app.db.database import get_db
from app.models import (
    POISchema,
    POIListResponse,
    UserSchema,
    TravelDiarySchema,
    TravelDiaryListResponse,
)

from app.services import (
    POIService,
    RouteService,
    RecommendationService,
    DiaryService,
)

router = APIRouter(prefix="/api", tags=["Travel System API"])

# Initialize services
poi_service = POIService()
diary_service = DiaryService()
recommendation_service = RecommendationService()

# Initialize route service with global graph
route_service = RouteService(poi_service.graph)


@router.on_event("startup")
async def startup_event(db: Session = Depends(get_db)):
    """Initialize indexes and data structures on startup"""
    pass


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


# ==================== User Endpoints ====================
@router.post("/users", response_model=UserSchema, tags=["User"])
def create_user(user: UserSchema, db: Session = Depends(get_db)):
    """Create a new user"""
    existing = crud.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    return crud.create_user(db, user)


@router.get("/users/{user_id}", response_model=UserSchema, tags=["User"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user details by ID"""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSchema.from_attributes(user) if hasattr(user, "__dict__") else user


# ==================== Diary Endpoints ====================
@router.post("/diaries", response_model=TravelDiarySchema, tags=["Diary"])
def create_diary(
    user_id: int = Query(..., gt=0),
    title: str = Query(..., min_length=1),
    content: str = Query(..., min_length=1),
    poi_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Create a new travel diary"""
    return diary_service.create_diary(db, user_id, title, content, poi_id)


@router.get("/diaries/{user_id}", response_model=TravelDiaryListResponse, tags=["Diary"])
def get_user_diaries(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all diaries for a user"""
    diaries = diary_service.get_user_diaries(db, user_id, skip, limit)
    return TravelDiaryListResponse(total=len(diaries), items=diaries)


@router.get("/diaries/{user_id}/search", response_model=list[TravelDiarySchema], tags=["Diary"])
def search_diaries(user_id: int, keyword: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search diaries by keyword"""
    return diary_service.search_diary_by_keyword(db, user_id, keyword)


# ==================== Recommendation Endpoints ====================
@router.get("/recommendations/top-k", response_model=list[dict], tags=["Recommendation"])
def get_top_pois(k: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Get Top-K POIs by score"""
    return recommendation_service.get_top_k_pois(db, k)


@router.get("/recommendations/users/{user_id}", response_model=list[dict], tags=["Recommendation"])
def recommend_for_user(user_id: int, k: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Get personalized recommendations for a user"""
    return recommendation_service.recommend_by_interest(db, user_id, k)


# ==================== Trip Generation Endpoint (simple)
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
    """Generate a simple trip plan. Currently returns a lightweight demo plan.

    This endpoint is a placeholder that frontend can call. Replace with
    a richer planner that uses `POIService`, `RouteService` and external
    LLM/knowledge graph services as needed.
    """
    # Minimal demo response structure matching frontend expectations
    demo = {
        "success": True,
        "message": "generated",
        "data": {
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "overall_suggestions": "这是一个来自后端的演示行程（可替换为真实生成器）",
            "weather_info": [],
            "budget": {
                "total_attractions": 1000,
                "total_hotels": 1500,
                "total_meals": 600,
                "total_transportation": 200,
                "total": 3300,
            },
            "days": [
                {
                    "date": start_date,
                    "day_index": 0,
                    "description": "到达并简单游览",
                    "transportation": transportation or "混合",
                    "accommodation": accommodation or "舒适型酒店",
                    "attractions": [],
                    "meals": [],
                }
            ],
        },
    }
    return demo
