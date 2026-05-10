"""Helper script: fetch TripStar XHS search/detail data in an isolated process."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

CITY_SEGMENT_SEPARATORS = ("-", "·", "/", "|", ",", "，", " ")


def _pick_query_city(city: str) -> str:
    raw = str(city or "").strip()
    if not raw:
        return ""

    split_candidates: list[str] = []
    pending = [raw]
    for separator in CITY_SEGMENT_SEPARATORS:
        next_pending: list[str] = []
        for item in pending:
            parts = [part.strip() for part in item.split(separator) if part.strip()]
            if len(parts) > 1:
                split_candidates.extend(parts)
                next_pending.extend(parts)
        pending.extend(next_pending)

    if not split_candidates:
        split_candidates = [raw]

    chinese_candidates = [item for item in split_candidates if any("\u4e00" <= ch <= "\u9fff" for ch in item)]
    if chinese_candidates:
        preferred = [item for item in chinese_candidates if item not in {"中国", "中华人民共和国"}]
        target = preferred or chinese_candidates
        return min(target, key=lambda x: (len(x), split_candidates.index(x)))

    return split_candidates[-1]


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def _build_query_candidates(city: str, keywords: str, poi_names: list[str]) -> list[str]:
    query_city = _pick_query_city(city) or city
    keyword_parts = [part.strip() for part in str(keywords or "").replace("，", " ").replace(",", " ").split() if part.strip()]
    poi_parts = [str(item).strip() for item in poi_names if str(item).strip()]

    candidates = [
        f"{query_city} {' '.join(keyword_parts[:2])} 旅游 景点攻略".strip(),
        f"{query_city} {' '.join(keyword_parts[:2])} 攻略".strip(),
        f"{query_city} {' '.join(poi_parts[:2])} 攻略".strip() if poi_parts else "",
        f"{query_city} 景点 推荐".strip(),
        f"{query_city} 一日游 攻略".strip(),
    ]

    deduped: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        normalized = " ".join(item.split()).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def _is_note_like_item(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    model_type = str(item.get("model_type") or "").strip().lower()
    if model_type in {"note", "note_v2", "normal_note", "search_note"}:
        return True
    note_card = item.get("note_card")
    if isinstance(note_card, dict):
        title = str(note_card.get("display_title") or note_card.get("title") or "").strip()
        return bool(title or note_card.get("desc") or item.get("id"))
    return bool(item.get("id") and item.get("xsec_token"))


def main() -> int:
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        _emit({"success": False, "message": "helper 输入不是合法 JSON"})
        return 1

    if not importlib.util.find_spec("execjs"):
        _emit({"success": False, "message": "当前 Python 环境未安装 execjs，无法调用 TripStar 原生小红书签名链路。"})
        return 1

    project_root = Path(str(payload.get("project_root") or "")).resolve()
    tripstar_backend = project_root / "TripStar" / "backend"
    if not tripstar_backend.exists():
        _emit({"success": False, "message": f"未找到 TripStar backend 目录: {tripstar_backend}"})
        return 1

    sys.path.insert(0, str(tripstar_backend))

    try:
        from app.services.xhs_service import XhsNativeClient  # type: ignore
    except Exception as exc:
        _emit({"success": False, "message": f"加载 TripStar 小红书服务失败: {exc}"})
        return 1

    city = str(payload.get("city") or "").strip()
    keywords = str(payload.get("keywords") or "").strip()
    poi_names = payload.get("poi_names") if isinstance(payload.get("poi_names"), list) else []
    cookie = str(payload.get("cookie") or "").strip()
    max_items = max(1, min(int(payload.get("max_items") or 4), 8))

    if not city:
        _emit({"success": False, "message": "city 不能为空"})
        return 1
    if not cookie:
        _emit({"success": False, "message": "cookie 不能为空"})
        return 1

    client = XhsNativeClient(cookie)
    query_candidates = _build_query_candidates(city, keywords, poi_names)
    query = query_candidates[0] if query_candidates else city
    search_response = {}
    last_error = ""
    for candidate in query_candidates:
        query = candidate
        try:
            search_response = client.search_notes(keyword=query, page_size=max_items)
            items = search_response.get("data", {}).get("items", [])
            if any(_is_note_like_item(item) for item in items if isinstance(item, dict)):
                break
        except Exception as exc:
            last_error = str(exc)
            continue
    else:
        if last_error:
            _emit({"success": False, "message": f"TripStar 搜索失败: {last_error}"})
            return 1

    items = search_response.get("data", {}).get("items", [])
    detail_items: list[dict] = []
    matched_count = 0
    model_types: list[str] = []
    preview_items: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        model_types.append(str(item.get("model_type") or ""))
        note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else {}
        preview_items.append(
            {
                "id": str(item.get("id") or "")[:24],
                "model_type": str(item.get("model_type") or ""),
                "title": str(note_card.get("display_title") or note_card.get("title") or item.get("title") or "")[:80],
                "keys": list(item.keys())[:8],
            }
        )
        if not _is_note_like_item(item):
            continue
        note_id = str(item.get("id") or "").strip()
        xsec_token = str(item.get("xsec_token") or "").strip()
        if not note_id:
            continue
        matched_count += 1
        try:
            detail_response = client.get_note_detail(note_id, xsec_token)
            detail_items.extend(detail_response.get("data", {}).get("items", []))
        except Exception:
            continue
        if matched_count >= max_items:
            break

    _emit(
        {
            "success": True,
            "query": query,
            "raw_note_count": matched_count,
            "data": {
                "city": city,
                "query_city": _pick_query_city(city) or city,
                "keywords": keywords,
                "query_candidates": query_candidates,
                "search_item_count": len(items),
                "search_model_types": model_types[:10],
                "search_item_preview": preview_items[:5],
                "search_response": search_response,
                "detail_response": {"data": {"items": detail_items}},
            },
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
