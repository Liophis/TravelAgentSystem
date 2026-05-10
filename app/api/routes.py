from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.heap import top_k
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
    XHSContentService,
    XHSLiveFetchError,
    XHSLiveFetchService,
)

router = APIRouter(prefix="/api", tags=["Travel System API"])

# Initialize services
poi_service = POIService()

# Initialize route service with global graph
route_service = RouteService(poi_service.graph)
xhs_content_service = XHSContentService()
xhs_live_fetch_service = XHSLiveFetchService()


class RuntimeSettingsPayload(BaseModel):
    """Runtime settings editable from the frontend."""

    api_base_url: Optional[str] = Field(default=None, description="Frontend API base URL")
    amap_web_api_key: Optional[str] = Field(default=None, description="AMap Web Service Key")
    vite_amap_web_js_key: Optional[str] = Field(default=None, description="AMap Web JS Key")
    google_maps_api_key: Optional[str] = Field(default=None, description="Google Maps API Key")
    google_maps_proxy: Optional[str] = Field(default=None, description="Google Maps Proxy")
    xhs_cookie: Optional[str] = Field(default=None, description="XHS Cookie")
    xhs_sample_notes_path: Optional[str] = Field(default=None, description="XHS sample notes JSON path")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI Base URL")
    openai_model: Optional[str] = Field(default=None, description="OpenAI Model")
    log_level: Optional[str] = Field(default=None, description="Log level")


class XHSImportPayload(BaseModel):
    """Payload for importing external XHS-like notes."""

    source_name: Optional[str] = Field(default=None, description="Imported file name")
    format_hint: Optional[str] = Field(default="auto", description="Optional import format hint")
    payload: dict | list = Field(..., description="Normalized notes, XHS raw results, TripStar bundle, or third-party payload")


class XHSRefreshPayload(BaseModel):
    """Payload for refreshing XHS content via TripStar live fetch."""

    city: str = Field(min_length=1, description="Target city")
    keywords: Optional[str] = Field(default="", description="Optional extra keywords")
    max_items: int = Field(default=4, ge=1, le=8, description="Max raw notes to fetch")


class XHSRefreshTripPayload(BaseModel):
    """Payload for refreshing XHS content and re-enriching the current trip plan."""

    trip_plan: dict = Field(..., description="Current trip plan")
    city: Optional[str] = Field(default=None, description="Target city override")
    keywords: Optional[str] = Field(default="", description="Optional extra keywords")
    max_items: int = Field(default=4, ge=1, le=8, description="Max raw notes to fetch")


INTEREST_KEYWORDS: dict[str, tuple[str, ...]] = {
    "历史文化": ("历史", "文化", "博物", "皇家", "建筑", "故宫", "长城", "广场"),
    "自然风光": ("自然", "风景", "公园", "园林", "长城"),
    "美食": ("美食", "餐", "小吃"),
    "购物": ("购物", "商场", "市集"),
    "艺术": ("艺术", "展览", "博物"),
    "休闲": ("休闲", "公园", "动物园", "漫步"),
}

CITY_ALIASES: dict[str, tuple[str, ...]] = {
    "beijing": ("beijing", "北京"),
    "tokyo": ("tokyo", "东京"),
    "xi'an": ("xian", "xi'an", "西安"),
}

CITY_SEGMENT_SEPARATORS = ("-", "·", "/", "|", ",", "，", " ")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371.0 * c


def _expand_city_tokens(city: str) -> set[str]:
    raw_city = city.strip()
    normalized = raw_city.lower()
    tokens = {normalized, raw_city}

    pending = {raw_city}
    for separator in CITY_SEGMENT_SEPARATORS:
        next_pending: set[str] = set()
        for item in pending:
            parts = [part.strip() for part in item.split(separator) if part.strip()]
            if len(parts) > 1:
                next_pending.update(parts)
        pending.update(next_pending)

    for item in list(pending):
        if item:
            tokens.add(item)
            tokens.add(item.lower())

    aliases = CITY_ALIASES.get(normalized, ())
    tokens.update(aliases)
    for item in list(pending):
        aliases = CITY_ALIASES.get(item.lower(), ())
        tokens.update(aliases)

    return {token for token in tokens if token}


def _normalize_preference_tokens(preferences: list[str] | None, free_text_input: str | None) -> list[str]:
    tokens = list(preferences or [])
    if free_text_input:
        tokens.extend(part for part in free_text_input.replace("，", " ").replace(",", " ").split() if part)
    return tokens


def _score_poi_for_trip(poi, city: str, preference_tokens: list[str]) -> float:
    haystack = " ".join(filter(None, [poi.name, poi.type, poi.description or ""])).lower()
    score = 20.0

    city_tokens = _expand_city_tokens(city)
    if any(token.lower() in haystack for token in city_tokens):
        score += 50.0

    for token in preference_tokens:
        token_lower = token.lower()
        if token_lower in haystack:
            score += 20.0

        for interest, keywords in INTEREST_KEYWORDS.items():
            if interest == token and any(keyword.lower() in haystack for keyword in keywords):
                score += 18.0

    if poi.type in {"景区", "景点"}:
        score += 8.0
    elif poi.type in {"公园", "动物园"}:
        score += 5.0

    score += max(0.0, 3.0 - poi.id * 0.01)
    return score


def _order_pois_for_route(pois: list[object], score_map: dict[int, float]) -> list[object]:
    if not pois:
        return []

    remaining = list(pois)
    remaining.sort(key=lambda item: score_map.get(item.id, 0.0), reverse=True)
    ordered = [remaining.pop(0)]

    while remaining:
        current = ordered[-1]
        next_poi = min(
            remaining,
            key=lambda item: _haversine_km(current.latitude, current.longitude, item.latitude, item.longitude),
        )
        ordered.append(next_poi)
        remaining.remove(next_poi)

    return ordered


def _build_trip_attraction(poi, city: str) -> dict:
    return {
        "id": poi.id,
        "name": poi.name,
        "type": poi.type,
        "category": poi.type,
        "address": f"{city} · {poi.name}",
        "latitude": poi.latitude,
        "longitude": poi.longitude,
        "location": {
            "latitude": poi.latitude,
            "longitude": poi.longitude,
        },
        "visit_duration": 90,
        "description": poi.description or "暂无景点描述",
        "ticket_price": 80 if poi.type in {"景区", "景点"} else 50,
        "estimated_cost": 80 if poi.type in {"景区", "景点"} else 50,
        "content_sources": [],
        "recommendation_reasons": [],
        "travel_notes": [],
    }


def _estimate_trip_budget(days: list[dict], accommodation: str, transportation: str) -> dict:
    accommodation_cost_map = {
        "经济型酒店": 220,
        "舒适型酒店": 360,
        "豪华酒店": 680,
        "民宿": 300,
    }
    transportation_multiplier = {
        "步行": 0.3,
        "公共交通": 0.8,
        "自驾": 1.3,
        "混合": 1.0,
    }

    total_attractions = int(
        sum(attraction.get("ticket_price", 0) for day in days for attraction in day.get("attractions", []))
    )
    total_meals = len(days) * 120
    total_hotels = len(days) * accommodation_cost_map.get(accommodation, 300)

    total_distance = 0.0
    for day in days:
        attractions = day.get("attractions", [])
        for current, nxt in zip(attractions, attractions[1:]):
            total_distance += _haversine_km(
                current["latitude"],
                current["longitude"],
                nxt["latitude"],
                nxt["longitude"],
            )

    total_transportation = int(max(30, total_distance * 12 * transportation_multiplier.get(transportation, 1.0)))
    total = total_attractions + total_hotels + total_meals + total_transportation

    return {
        "total_attractions": total_attractions,
        "total_hotels": total_hotels,
        "total_meals": total_meals,
        "total_transportation": total_transportation,
        "total": total,
    }


def _build_trip_suggestion(city: str, selected_pois: list[object], requested_city_matched: bool) -> str:
    attraction_names = "、".join(poi.name for poi in selected_pois[:4]) if selected_pois else "暂无景点"
    if requested_city_matched:
        return f"本次为你优先围绕 {city} 生成了轻量行程，重点包含 {attraction_names}。"
    return (
        f"当前本地样例数据暂未完整覆盖 {city}，系统已使用现有景点样例为你生成可演示闭环。"
        f" 当前重点景点包括 {attraction_names}。"
    )


def _build_attraction_reasons(poi, city: str, preference_tokens: list[str], related_notes: list[dict]) -> list[str]:
    reasons: list[str] = []
    if city and city.lower() in str(getattr(poi, "city", "")).lower():
        reasons.append(f"景点位于 {city} 本地候选范围内，更适合直接纳入当前行程。")

    matched_preferences = [
        token for token in preference_tokens if token and token.lower() in f"{poi.name} {poi.type} {poi.description or ''}".lower()
    ]
    if matched_preferences:
        reasons.append(f"景点内容与偏好 {'、'.join(dict.fromkeys(matched_preferences[:3]))} 有直接关联。")

    if related_notes:
        note = related_notes[0]
        match_reason = str(note.get("match_reason") or "").strip()
        if match_reason:
            reasons.append(match_reason)
        highlights = note.get("highlights") or []
        if highlights:
            reasons.append(str(highlights[0]))

    if not reasons:
        reasons.append("该景点已在当前候选集中按城市、类型与说明信息综合排序。")

    return reasons[:4]


def _build_trip_recommendation_reasons(
    *,
    city: str,
    actual_days: int,
    attraction_count: int,
    preferences: list[str] | None,
    requested_city_matched: bool,
    content_bundle: dict,
) -> list[str]:
    reasons = [f"本次先围绕 {city} 的可用景点候选生成 {actual_days} 天行程，当前共安排 {attraction_count} 个景点。"]
    if preferences:
        reasons.append(f"推荐时已纳入你的偏好：{'、'.join(preferences)}。")
    if requested_city_matched:
        reasons.append("已优先命中目标城市本地景点数据，因此结果更贴近城市内真实游览。")
    else:
        reasons.append("目标城市样例暂不完整，系统使用现有本地景点库维持主闭环可用。")

    sources = content_bundle.get("sources") or []
    if sources:
        source_labels = "、".join(source.get("source_label", "内容来源") for source in sources)
        if content_bundle.get("uses_fallback"):
            reasons.append(f"内容增强当前来自 {source_labels} 的本地样例，外部内容失败时会自动降级，不阻塞行程生成。")
        else:
            reasons.append(f"推荐理由已合并 {source_labels} 的内容摘要，用于补充亮点和避坑信息。")

    return reasons[:5]


def _extract_trip_plan_preferences(trip_plan: dict) -> list[str]:
    request_summary = trip_plan.get("request_summary")
    if isinstance(request_summary, dict):
        preferences = request_summary.get("preferences")
        if isinstance(preferences, list):
            return [str(item).strip() for item in preferences if str(item).strip()]
    return []


def _extract_trip_plan_poi_stubs(trip_plan: dict) -> list[object]:
    poi_stubs: list[object] = []
    seen_keys: set[str] = set()
    for day in trip_plan.get("days", []) if isinstance(trip_plan.get("days"), list) else []:
        attractions = day.get("attractions")
        if not isinstance(attractions, list):
            continue
        for attraction in attractions:
            if not isinstance(attraction, dict):
                continue
            name = str(attraction.get("name") or "").strip()
            if not name:
                continue
            key = f"{name}|{attraction.get('latitude')}|{attraction.get('longitude')}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            poi_stubs.append(
                type(
                    "TripAttractionStub",
                    (),
                    {
                        "name": name,
                        "city": str(trip_plan.get("city") or "").strip(),
                        "type": str(attraction.get("type") or attraction.get("category") or "景点").strip(),
                        "description": str(attraction.get("description") or "").strip(),
                    },
                )()
            )
    return poi_stubs


def _extract_trip_plan_poi_names(trip_plan: dict) -> list[str]:
    return [str(getattr(poi, "name", "")).strip() for poi in _extract_trip_plan_poi_stubs(trip_plan) if str(getattr(poi, "name", "")).strip()]


def _refresh_trip_plan_xhs_enrichment(trip_plan: dict) -> dict:
    city = str(trip_plan.get("city") or "").strip()
    preferences = _extract_trip_plan_preferences(trip_plan)
    poi_stubs = _extract_trip_plan_poi_stubs(trip_plan)
    preference_tokens = _normalize_preference_tokens(preferences, None)
    content_bundle = xhs_content_service.enrich_trip_plan(city=city, preferences=preferences, pois=poi_stubs)
    city_tokens = {token.lower() for token in _expand_city_tokens(city)}
    requested_city_matched = any(
        str(getattr(poi, "city", "")).strip().lower() in city_tokens
        for poi in poi_stubs
        if str(getattr(poi, "city", "")).strip()
    )

    days = trip_plan.get("days")
    if isinstance(days, list):
        for day in days:
            attractions = day.get("attractions")
            if not isinstance(attractions, list):
                continue
            for attraction in attractions:
                if not isinstance(attraction, dict):
                    continue
                poi_name = str(attraction.get("name") or "").strip()
                related_notes = content_bundle["notes_by_poi"].get(poi_name, [])[:2]
                poi_stub = type(
                    "TripAttractionReasonStub",
                    (),
                    {
                        "name": poi_name,
                        "city": city,
                        "type": str(attraction.get("type") or attraction.get("category") or "景点").strip(),
                        "description": str(attraction.get("description") or "").strip(),
                    },
                )()
                attraction["travel_notes"] = related_notes
                attraction["content_sources"] = [
                    {
                        "source_type": note.get("source_type", "content"),
                        "source_label": note.get("source_label", "内容来源"),
                        "origin": note.get("origin", "local_sample"),
                    }
                    for note in related_notes
                ]
                attraction["recommendation_reasons"] = _build_attraction_reasons(
                    poi_stub,
                    city,
                    preference_tokens,
                    related_notes,
                )
                first_image = next(
                    (image.get("url") for note in related_notes for image in note.get("images", []) if image.get("url")),
                    "",
                )
                if first_image:
                    attraction["image_url"] = first_image

    trip_plan["content_sources"] = content_bundle["sources"]
    trip_plan["recommendation_reasons"] = _build_trip_recommendation_reasons(
        city=city,
        actual_days=len(days) if isinstance(days, list) else 0,
        attraction_count=len(_extract_trip_plan_poi_stubs(trip_plan)),
        preferences=preferences,
        requested_city_matched=requested_city_matched,
        content_bundle=content_bundle,
    )
    request_summary = trip_plan.get("request_summary")
    if isinstance(request_summary, dict):
        request_summary["data_mode"] = "city_match" if requested_city_matched else "local_sample"
        request_summary["data_note"] = (
            f"已按 {city} 本地样例景点生成计划。"
            if requested_city_matched
            else f"{city} 当前没有完整本地景点库，已使用现有样例数据生成计划。"
        )
    return trip_plan


def _build_request_summary(
    *,
    city: str,
    actual_days: int,
    transportation: str,
    accommodation: str,
    preferences: list[str] | None,
    free_text_input: str | None,
    requested_city_matched: bool,
) -> dict:
    return {
        "city": city,
        "travel_days": actual_days,
        "transportation": transportation,
        "accommodation": accommodation,
        "preferences": preferences or [],
        "free_text_input": free_text_input or "",
        "data_mode": "city_match" if requested_city_matched else "local_sample",
        "data_note": (
            f"已按 {city} 本地样例景点生成计划。"
            if requested_city_matched
            else f"{city} 当前没有完整本地景点库，已使用现有样例数据生成计划。"
        ),
    }


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


@router.get("/xhs/content-source", tags=["XHS Content"])
def get_xhs_content_source_status():
    return {
        "success": True,
        "message": "ok",
        "data": xhs_content_service.get_content_source_status(),
    }


@router.post("/xhs/content-source/import", tags=["XHS Content"])
def import_xhs_content_source(payload: XHSImportPayload):
    try:
        status = xhs_content_service.import_notes(
            payload.payload,
            source_name=payload.source_name or "",
            format_hint=payload.format_hint or "auto",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "外部内容样例已导入",
        "data": status,
    }


@router.delete("/xhs/content-source/import", tags=["XHS Content"])
def clear_xhs_content_source_import():
    return {
        "success": True,
        "message": "已清除导入的外部样例",
        "data": xhs_content_service.clear_imported_notes(),
    }


@router.post("/xhs/content-source/refresh", tags=["XHS Content"])
def refresh_xhs_content_source(payload: XHSRefreshPayload):
    try:
        refreshed = xhs_live_fetch_service.refresh_from_tripstar(
            city=payload.city,
            keywords=payload.keywords or "",
            poi_names=[],
            max_items=payload.max_items,
        )
    except XHSLiveFetchError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                **(exc.detail or {}),
            },
        ) from exc

    return {
        "success": True,
        "message": "已通过 TripStar 实时刷新小红书内容源",
        "data": refreshed["status"],
        "meta": {
            "query": refreshed["query"],
            "raw_note_count": refreshed["raw_note_count"],
        },
    }


@router.post("/xhs/content-source/refresh-trip", tags=["XHS Content"])
def refresh_xhs_trip_content(payload: XHSRefreshTripPayload):
    trip_plan = payload.trip_plan or {}
    if not trip_plan:
        raise HTTPException(status_code=400, detail="trip_plan 不能为空")

    city = (payload.city or trip_plan.get("city") or "").strip()
    if not city:
        raise HTTPException(status_code=400, detail="无法从当前行程中识别城市")

    try:
        refreshed = xhs_live_fetch_service.refresh_from_tripstar(
            city=city,
            keywords=payload.keywords or "",
            poi_names=_extract_trip_plan_poi_names(trip_plan),
            max_items=payload.max_items,
        )
    except XHSLiveFetchError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                **(exc.detail or {}),
            },
        ) from exc

    updated_trip_plan = _refresh_trip_plan_xhs_enrichment(dict(trip_plan))
    return {
        "success": True,
        "message": "已刷新 XHS 内容并重生成推荐理由",
        "data": updated_trip_plan,
        "meta": {
            "query": refreshed["query"],
            "raw_note_count": refreshed["raw_note_count"],
            "content_source_status": refreshed["status"],
        },
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
                city=poi.city,
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
    preferences: list[str] | None = Query(None),
    free_text_input: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Generate a lightweight real trip plan from current local POI data."""
    pois = crud.get_all_pois(db, skip=0, limit=200)
    if not pois:
        raise HTTPException(status_code=404, detail="No POI data available")

    try:
        parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
        parsed_end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD") from exc

    requested_days = max(1, travel_days)
    date_span_days = max(1, (parsed_end - parsed_start).days + 1)
    actual_days = min(requested_days, date_span_days)

    preference_tokens = _normalize_preference_tokens(preferences, free_text_input)
    city_tokens = _expand_city_tokens(city)
    city_matched_pois = [
        poi for poi in pois
        if poi.city.lower() in {token.lower() for token in city_tokens}
    ]
    candidate_pois = city_matched_pois or pois
    requested_city_matched = bool(city_matched_pois)
    content_bundle = xhs_content_service.enrich_trip_plan(city=city, preferences=preferences, pois=candidate_pois)

    scored_candidates = [
        (_score_poi_for_trip(poi, city, preference_tokens), poi)
        for poi in candidate_pois
    ]
    selected_count = min(len(candidate_pois), max(actual_days * 2, actual_days))
    selected_ranked = top_k(scored_candidates, selected_count)
    selected_pois = [poi for _, poi in selected_ranked]
    score_map = {poi.id: score for score, poi in selected_ranked}
    ordered_pois = _order_pois_for_route(selected_pois, score_map)

    bucket_sizes = [len(ordered_pois) // actual_days] * actual_days
    for index in range(len(ordered_pois) % actual_days):
        bucket_sizes[index] += 1

    days: list[dict] = []
    cursor = 0
    current_date = parsed_start
    normalized_transportation = transportation or "混合"
    normalized_accommodation = accommodation or "舒适型酒店"

    for day_index, bucket_size in enumerate(bucket_sizes):
        day_pois = ordered_pois[cursor: cursor + bucket_size]
        cursor += bucket_size
        attractions = [_build_trip_attraction(poi, city) for poi in day_pois]
        for attraction, poi in zip(attractions, day_pois):
            related_notes = content_bundle["notes_by_poi"].get(poi.name, [])[:2]
            attraction["travel_notes"] = related_notes
            attraction["content_sources"] = [
                {
                    "source_type": note.get("source_type", "content"),
                    "source_label": note.get("source_label", "内容来源"),
                    "origin": note.get("origin", "local_sample"),
                }
                for note in related_notes
            ]
            attraction["recommendation_reasons"] = _build_attraction_reasons(poi, city, preference_tokens, related_notes)
            first_image = next(
                (image.get("url") for note in related_notes for image in note.get("images", []) if image.get("url")),
                "",
            )
            if first_image:
                attraction["image_url"] = first_image
        attraction_names = "、".join(item["name"] for item in attractions) if attractions else "自由活动"

        days.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_index": day_index,
            "description": f"第 {day_index + 1} 天重点安排：{attraction_names}",
            "transportation": normalized_transportation,
            "accommodation": normalized_accommodation,
            "attractions": attractions,
            "meals": [],
        })
        current_date += timedelta(days=1)

    budget = _estimate_trip_budget(days, normalized_accommodation, normalized_transportation)
    overall_suggestions = _build_trip_suggestion(city, ordered_pois, requested_city_matched)
    recommendation_reasons = _build_trip_recommendation_reasons(
        city=city,
        actual_days=actual_days,
        attraction_count=len(ordered_pois),
        preferences=preferences,
        requested_city_matched=requested_city_matched,
        content_bundle=content_bundle,
    )
    request_summary = _build_request_summary(
        city=city,
        actual_days=actual_days,
        transportation=normalized_transportation,
        accommodation=normalized_accommodation,
        preferences=preferences,
        free_text_input=free_text_input,
        requested_city_matched=requested_city_matched,
    )

    return {
        "success": True,
        "message": "generated",
        "data": {
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "overall_suggestions": overall_suggestions,
            "weather_info": [],
            "budget": budget,
            "request_summary": request_summary,
            "content_sources": content_bundle["sources"],
            "recommendation_reasons": recommendation_reasons,
            "days": days,
        },
    }


@router.post("/chat/ask", response_model=TripChatResponse, tags=["Trip Chat"])
def ask_trip_chat(payload: TripChatRequest):
    """Answer follow-up questions based on the current trip plan."""
    reply = answer_trip_question(
        message=payload.message,
        trip_plan=payload.trip_plan,
        history=[item.model_dump() for item in payload.history],
    )
    return TripChatResponse(success=True, reply=reply)
