import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import Destination, User, UserInterest, UserProfile
from app.seed.sample_data import INTEREST_TAGS
from app.services.llm_client_service import LLMClientError, chat_completion_text
from app.services.user_service import get_user_profile_from_db


LLMCall = Callable[..., str]


def extract_user_profile_with_llm_from_db(
    session: Session,
    user_id: int,
    llm_call: LLMCall | None = None,
) -> dict[str, Any] | None:
    user = _load_user_with_activity(session, user_id)
    if user is None:
        return None

    evidence = _collect_evidence(session, user)
    provider_error: str | None = None
    fallback_used = False
    raw_model_text = ""
    started_at = datetime.now(timezone.utc)
    call = llm_call or chat_completion_text

    try:
        raw_model_text = call(
            system_prompt=_build_system_prompt(),
            user_prompt=_build_user_prompt(user, evidence),
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        analysis = _parse_llm_json(raw_model_text)
    except (LLMClientError, ValueError, TypeError, json.JSONDecodeError) as exc:
        fallback_used = True
        provider_error = str(exc)
        analysis = _fallback_analysis(evidence)

    normalized = _normalize_analysis(analysis, evidence)
    elapsed_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    trace = {
        "stage": "stage-43-llm-user-profile",
        "algorithm": "LLM JSON extraction with deterministic tag aggregation fallback",
        "provider": "openai-compatible" if not fallback_used else "deterministic-fallback",
        "model": settings.llm_model,
        "fallback_used": str(fallback_used).lower(),
        "evidence_items": str(len(evidence)),
        "allowed_tags": str(len(INTEREST_TAGS)),
        "extracted_tags": str(len(normalized["tags"])),
        "elapsed_ms": str(elapsed_ms),
    }
    if provider_error:
        trace["provider_error"] = provider_error[:160]
    if raw_model_text:
        trace["llm_response_chars"] = str(len(raw_model_text))

    profile = _ensure_profile(session, user)
    profile.llm_profile_summary = normalized["summary"]
    profile.llm_profile_tags_json = json.dumps(normalized["tags"], ensure_ascii=False)
    profile.llm_profile_weights_json = json.dumps(normalized["weights"], ensure_ascii=False, sort_keys=True)
    profile.llm_profile_evidence_json = json.dumps(normalized["evidence"], ensure_ascii=False)
    profile.llm_profile_trace_json = json.dumps(trace, ensure_ascii=False, sort_keys=True)
    profile.llm_profile_updated_at = datetime.now(timezone.utc)
    _replace_user_interests(session, user.id, normalized["tags"])
    session.commit()

    return _build_analysis_payload(session, user.id, normalized, trace)


def get_user_profile_analysis_from_db(session: Session, user_id: int) -> dict[str, Any] | None:
    user = _load_user_with_activity(session, user_id)
    if user is None:
        return None
    profile = _ensure_profile(session, user)
    tags = _json_or_default(profile.llm_profile_tags_json, [])
    weights = _json_or_default(profile.llm_profile_weights_json, {})
    evidence = _json_or_default(profile.llm_profile_evidence_json, [])
    trace = _json_or_default(profile.llm_profile_trace_json, {})
    normalized = {
        "tags": [tag for tag in tags if isinstance(tag, str)],
        "weights": {str(key): float(value) for key, value in weights.items()} if isinstance(weights, dict) else {},
        "summary": profile.llm_profile_summary or "尚未进行 AI 画像分析。",
        "evidence": [item for item in evidence if isinstance(item, str)],
        "updated_at": profile.llm_profile_updated_at.isoformat() if profile.llm_profile_updated_at else None,
    }
    if not trace:
        trace = {
            "stage": "stage-43-llm-user-profile",
            "status": "not_analyzed",
            "fallback_used": "false",
        }
    return _build_analysis_payload(session, user.id, normalized, trace)


def _load_user_with_activity(session: Session, user_id: int) -> User | None:
    return session.scalar(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.interests),
            selectinload(User.favorites),
            selectinload(User.ratings),
            selectinload(User.behavior_logs),
        )
        .where(User.id == user_id)
    )


def _collect_evidence(session: Session, user: User) -> list[dict[str, Any]]:
    target_ids = {
        item.target_id
        for item in [*user.favorites, *user.ratings, *user.behavior_logs]
        if item.target_type == "destination"
    }
    destinations = {
        destination.id: destination
        for destination in session.scalars(
            select(Destination)
            .options(selectinload(Destination.tags))
            .where(Destination.id.in_(target_ids) if target_ids else False)
        ).all()
    }
    evidence: list[dict[str, Any]] = []
    for favorite in sorted(user.favorites, key=lambda item: item.created_at, reverse=True):
        if favorite.target_type != "destination":
            continue
        destination = destinations.get(favorite.target_id)
        evidence.append(_destination_evidence("favorite", destination, note=favorite.note, weight=3.0))
    for rating in sorted(user.ratings, key=lambda item: item.updated_at, reverse=True):
        if rating.target_type != "destination":
            continue
        destination = destinations.get(rating.target_id)
        weight = 2.6 if rating.rating >= 4 else 1.2
        evidence.append(_destination_evidence("rating", destination, note=f"rating={rating.rating}", weight=weight))
    for log in sorted(user.behavior_logs, key=lambda item: item.created_at, reverse=True):
        if log.target_type != "destination":
            continue
        destination = destinations.get(log.target_id)
        action_weight = {"recommend_click": 1.7, "route": 1.6, "search": 1.4, "view": 1.0}.get(log.action, 0.8)
        evidence.append(_destination_evidence(log.action, destination, note=log.metadata_text, weight=action_weight))

    current_interests = [interest.tag for interest in user.interests]
    if current_interests:
        evidence.append(
            {
                "action": "manual_interests",
                "name": "用户手动兴趣",
                "tags": current_interests,
                "note": ",".join(current_interests),
                "weight": 1.4,
            }
        )
    return evidence[:40]


def _destination_evidence(
    action: str,
    destination: Destination | None,
    note: str | None,
    weight: float,
) -> dict[str, Any]:
    if destination is None:
        return {"action": action, "name": "未知目的地", "tags": [], "note": note or "", "weight": weight}
    return {
        "action": action,
        "name": destination.name,
        "category": destination.category,
        "rating": destination.rating,
        "popularity": destination.popularity,
        "tags": [tag.tag for tag in destination.tags],
        "note": note or "",
        "weight": weight,
    }


def _build_system_prompt() -> str:
    return (
        "You are a user profile extraction service for a travel recommendation system. "
        "Return only JSON. Pick tags only from the allowed tag list. "
        "Do not invent tags. Weights must be numbers between 0 and 1."
    )


def _build_user_prompt(user: User, evidence: list[dict[str, Any]]) -> str:
    payload = {
        "user": {"id": user.id, "username": user.username, "nickname": user.profile.nickname if user.profile else user.username},
        "allowed_tags": INTEREST_TAGS,
        "evidence": evidence,
        "required_json_schema": {
            "tags": ["history", "campus"],
            "weights": {"history": 0.86, "campus": 0.72},
            "summary": "short Chinese profile summary",
            "evidence": ["short Chinese evidence sentence"],
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _parse_llm_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if "\n" in stripped:
            stripped = stripped.split("\n", 1)[1]
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON root must be an object.")
    return parsed


def _fallback_analysis(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    scores: Counter[str] = Counter()
    for item in evidence:
        weight = float(item.get("weight") or 1)
        for tag in item.get("tags", []):
            if tag in INTEREST_TAGS:
                scores[tag] += weight
    if not scores:
        scores.update({"culture": 1.0, "campus": 0.8, "food": 0.6})
    max_score = max(scores.values(), default=1)
    tags = [tag for tag, _ in scores.most_common(6)]
    evidence_text = [_format_evidence_text(item) for item in evidence[:6]]
    return {
        "tags": tags,
        "weights": {tag: round(scores[tag] / max_score, 2) for tag in tags},
        "summary": f"根据收藏、评分和浏览记录，用户更偏好 {', '.join(tags[:3])} 类型目的地。",
        "evidence": evidence_text or ["暂无足够行为，使用默认兴趣画像。"],
    }


def _normalize_analysis(analysis: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    allowed = set(INTEREST_TAGS)
    tags = []
    for tag in analysis.get("tags", []):
        if isinstance(tag, str) and tag in allowed and tag not in tags:
            tags.append(tag)
    weights: dict[str, float] = {}
    raw_weights = analysis.get("weights", {})
    if isinstance(raw_weights, dict):
        for tag in tags:
            value = raw_weights.get(tag, 0.65)
            try:
                weights[tag] = round(max(0, min(float(value), 1)), 2)
            except (TypeError, ValueError):
                weights[tag] = 0.65
    if not tags:
        return _normalize_analysis(_fallback_analysis(evidence), evidence)
    for tag in tags:
        weights.setdefault(tag, 0.65)
    summary = str(analysis.get("summary") or f"用户当前主要兴趣为 {', '.join(tags[:3])}。")[:300]
    evidence_text = analysis.get("evidence", [])
    if not isinstance(evidence_text, list):
        evidence_text = []
    normalized_evidence = [str(item)[:160] for item in evidence_text if str(item).strip()][:8]
    if not normalized_evidence:
        normalized_evidence = [_format_evidence_text(item) for item in evidence[:6]]
    return {
        "tags": tags[:8],
        "weights": {tag: weights[tag] for tag in tags[:8]},
        "summary": summary,
        "evidence": normalized_evidence,
    }


def _format_evidence_text(item: dict[str, Any]) -> str:
    action = str(item.get("action") or "behavior")
    name = str(item.get("name") or "未知目的地")
    tags = item.get("tags", [])
    tag_text = ",".join(tags[:3]) if isinstance(tags, list) else ""
    return f"{action}: {name}" + (f" -> {tag_text}" if tag_text else "")


def _ensure_profile(session: Session, user: User) -> UserProfile:
    if user.profile is not None:
        return user.profile
    profile = UserProfile(user_id=user.id, nickname=user.username, avatar_url=None)
    session.add(profile)
    session.flush()
    return profile


def _replace_user_interests(session: Session, user_id: int, tags: list[str]) -> None:
    session.execute(delete(UserInterest).where(UserInterest.user_id == user_id))
    for tag in tags:
        session.add(UserInterest(user_id=user_id, tag=tag))


def _json_or_default(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _build_analysis_payload(
    session: Session,
    user_id: int,
    normalized: dict[str, Any],
    trace: dict[str, str],
) -> dict[str, Any]:
    updated_profile = get_user_profile_from_db(session, user_id)
    return {
        "user_id": user_id,
        "tags": normalized["tags"],
        "weights": normalized["weights"],
        "summary": normalized["summary"],
        "evidence": normalized["evidence"],
        "updated_at": normalized.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        "updated_profile": updated_profile,
        "algorithm_trace": trace,
    }
