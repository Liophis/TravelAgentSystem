"""Xiaohongshu-inspired content enrichment service for P1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import get_settings


BUILTIN_XHS_NOTES: list[dict[str, Any]] = [
    {
        "id": "xhs-local-beijing-gugong",
        "source_type": "xhs",
        "source_label": "小红书公开内容",
        "origin": "local_sample",
        "title": "北京故宫半日游路线整理",
        "city": "北京",
        "poi_name": "故宫博物院",
        "author": "TripStar Lab",
        "tags": ["历史文化", "故宫", "拍照", "避坑"],
        "images": [
            {
                "url": "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=900&q=80",
                "alt": "故宫宫墙与建筑",
            }
        ],
        "highlights": ["中轴线建筑群非常集中，适合第一次到北京的用户。", "上午入园更容易避开高峰。"],
        "cautions": ["节假日建议提前预约。", "步行距离较长，建议穿舒适鞋。"],
        "excerpt": "适合把故宫放在上午主线，搭配周边历史文化景点形成连续体验。",
        "match_reason": "与历史文化偏好和北京核心景点强相关。",
    },
    {
        "id": "xhs-local-beijing-yiheyuan",
        "source_type": "xhs",
        "source_label": "小红书公开内容",
        "origin": "local_sample",
        "title": "颐和园慢节奏散步攻略",
        "city": "北京",
        "poi_name": "颐和园",
        "author": "TripStar Lab",
        "tags": ["自然风光", "休闲", "园林"],
        "images": [
            {
                "url": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?auto=format&fit=crop&w=900&q=80",
                "alt": "园林与湖景",
            }
        ],
        "highlights": ["适合半天到一天的放松游览。", "园林和湖景对休闲偏好更友好。"],
        "cautions": ["园区较大，建议预留充足步行时间。"],
        "excerpt": "如果你想把北京行程做得不那么紧，颐和园很适合作为节奏调节点。",
        "match_reason": "匹配休闲和自然风光类偏好。",
    },
    {
        "id": "xhs-local-beijing-zoo",
        "source_type": "xhs",
        "source_label": "小红书公开内容",
        "origin": "local_sample",
        "title": "北京动物园亲子轻松线",
        "city": "北京",
        "poi_name": "北京动物园",
        "author": "TripStar Lab",
        "tags": ["休闲", "亲子", "动物园"],
        "images": [],
        "highlights": ["动线清晰，适合轻松半日安排。"],
        "cautions": ["周末人流可能较多。"],
        "excerpt": "更适合把它放在不追求高密度打卡的一天。",
        "match_reason": "适合休闲与轻量节奏路线。",
    },
]


class XHSContentService:
    """Provide stable content structures and graceful fallback for P1."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _load_external_candidates(self) -> list[dict[str, Any]]:
        sample_path = (self.settings.xhs_sample_notes_path or "").strip()
        if not sample_path:
            return []

        try:
            payload = json.loads(Path(sample_path).read_text(encoding="utf-8"))
        except Exception:
            return []

        if not isinstance(payload, list):
            return []

        normalized: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict):
                normalized.append(self._normalize_note(item, default_origin="external"))
        return normalized

    def _normalize_note(self, item: dict[str, Any], *, default_origin: str) -> dict[str, Any]:
        title = str(item.get("title") or item.get("poi_name") or item.get("city") or "旅行内容").strip()
        poi_name = str(item.get("poi_name") or item.get("poi") or "").strip()
        city = str(item.get("city") or "").strip()

        raw_images = item.get("images")
        images: list[dict[str, str]] = []
        if isinstance(raw_images, list):
            for image in raw_images:
                if isinstance(image, str) and image.strip():
                    images.append({"url": image.strip(), "alt": title})
                elif isinstance(image, dict) and str(image.get("url") or "").strip():
                    images.append({
                        "url": str(image.get("url")).strip(),
                        "alt": str(image.get("alt") or title).strip(),
                    })

        def _normalize_text_list(value: Any) -> list[str]:
            if isinstance(value, list):
                return [str(entry).strip() for entry in value if str(entry).strip()]
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            return []

        return {
            "id": str(item.get("id") or f"xhs-{city or 'unknown'}-{poi_name or title}").strip(),
            "source_type": "xhs",
            "source_label": str(item.get("source_label") or "小红书公开内容").strip(),
            "origin": str(item.get("origin") or default_origin).strip() or default_origin,
            "title": title,
            "city": city,
            "poi_name": poi_name,
            "author": str(item.get("author") or "").strip(),
            "tags": _normalize_text_list(item.get("tags")),
            "images": images,
            "highlights": _normalize_text_list(item.get("highlights")),
            "cautions": _normalize_text_list(item.get("cautions")),
            "excerpt": str(item.get("excerpt") or "").strip(),
            "match_reason": str(item.get("match_reason") or "").strip(),
            "note_url": str(item.get("note_url") or "").strip(),
        }

    def _match_notes(
        self,
        notes: list[dict[str, Any]],
        *,
        city: str,
        pois: list[object],
        keywords: list[str],
    ) -> list[dict[str, Any]]:
        city_lower = city.strip().lower()
        poi_names = {str(getattr(poi, "name", "")).strip().lower() for poi in pois if getattr(poi, "name", None)}
        keyword_tokens = {token.strip().lower() for token in keywords if token and token.strip()}

        ranked: list[tuple[int, dict[str, Any]]] = []
        for raw_note in notes:
            note = self._normalize_note(raw_note, default_origin="external")
            haystack = " ".join(
                [
                    note.get("title") or "",
                    note.get("city") or "",
                    note.get("poi_name") or "",
                    note.get("excerpt") or "",
                    " ".join(note.get("tags") or []),
                    " ".join(note.get("highlights") or []),
                ]
            ).lower()

            score = 0
            if (note.get("city") or "").lower() == city_lower:
                score += 5
            if (note.get("poi_name") or "").lower() in poi_names:
                score += 6
            for token in keyword_tokens:
                if token in haystack:
                    score += 2

            if score > 0:
                ranked.append((score, note))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [note for _, note in ranked[:8]]

    def _search_builtin_candidates(self, city: str, pois: list[object], keywords: list[str]) -> list[dict[str, Any]]:
        return self._match_notes(BUILTIN_XHS_NOTES, city=city, pois=pois, keywords=keywords)

    def get_content_candidates(self, city: str, preferences: list[str] | None, pois: list[object]) -> list[dict[str, Any]]:
        keywords = [city, *(preferences or []), *(str(getattr(poi, "name", "")).strip() for poi in pois)]

        external_notes = self._load_external_candidates()
        matched_external = self._match_notes(external_notes, city=city, pois=pois, keywords=keywords)
        if matched_external:
            return matched_external

        return self._search_builtin_candidates(city, pois, keywords)

    def enrich_trip_plan(self, *, city: str, preferences: list[str] | None, pois: list[object]) -> dict[str, Any]:
        notes = self.get_content_candidates(city, preferences, pois)
        notes_by_poi: dict[str, list[dict[str, Any]]] = {}
        for note in notes:
            poi_key = str(note.get("poi_name") or "").strip()
            if poi_key:
                notes_by_poi.setdefault(poi_key, []).append(note)

        unique_sources: dict[tuple[str, str, str], dict[str, Any]] = {}
        for note in notes:
            source_key = (
                str(note.get("source_type") or ""),
                str(note.get("source_label") or ""),
                str(note.get("origin") or ""),
            )
            unique_sources[source_key] = {
                "source_type": source_key[0] or "content",
                "source_label": source_key[1] or "内容来源",
                "origin": source_key[2] or "local_sample",
            }

        return {
            "notes": notes,
            "notes_by_poi": notes_by_poi,
            "sources": list(unique_sources.values()),
            "uses_fallback": all((source.get("origin") == "local_sample") for source in unique_sources.values()) if unique_sources else True,
        }
