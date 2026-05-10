"""Xiaohongshu-inspired content enrichment service for P1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime, UTC

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
        self.runtime_notes_path = Path(__file__).resolve().parents[2] / "runtime_xhs_notes.json"
        self.runtime_meta_path = Path(__file__).resolve().parents[2] / "runtime_xhs_notes.meta.json"

    def _read_json_file(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def normalize_xhs_cookie(self, cookie: str) -> str:
        """兼容 TripStar 使用的 Cookie 请求头字符串和浏览器导出的 JSON Cookie 列表。"""
        normalized = str(cookie or "").strip()
        if not normalized:
            return ""

        if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"'", '"'}:
            normalized = normalized[1:-1].strip()

        cookie_items = None
        if normalized.startswith("[") and normalized.endswith("]"):
            try:
                cookie_items = json.loads(normalized)
            except json.JSONDecodeError:
                cookie_items = None
        elif normalized.startswith("{") and '"name"' in normalized and '"value"' in normalized:
            try:
                cookie_items = json.loads(f"[{normalized}]")
            except json.JSONDecodeError:
                cookie_items = None

        if isinstance(cookie_items, list):
            pairs = []
            for item in cookie_items:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                value = str(item.get("value", "")).strip()
                if name:
                    pairs.append(f"{name}={value}")
            if pairs:
                return "; ".join(pairs)

        return normalized

    def _normalize_text_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(entry).strip() for entry in value if str(entry).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def _normalize_image_list(self, value: Any, *, default_alt: str) -> list[dict[str, str]]:
        images: list[dict[str, str]] = []
        if isinstance(value, list):
            for image in value:
                if isinstance(image, str) and image.strip():
                    images.append({"url": image.strip(), "alt": default_alt})
                elif isinstance(image, dict):
                    url = str(
                        image.get("url")
                        or image.get("src")
                        or image.get("image_url")
                        or image.get("url_default")
                        or ""
                    ).strip()
                    if url:
                        images.append({
                            "url": url,
                            "alt": str(image.get("alt") or default_alt).strip(),
                        })
        elif isinstance(value, dict):
            return self._normalize_image_list([value], default_alt=default_alt)
        return images

    def _extract_city_from_text(self, item: dict[str, Any], context: dict[str, Any]) -> str:
        for key in ("city", "city_name", "destination", "target_city"):
            value = str(item.get(key) or context.get(key) or "").strip()
            if value:
                return value
        return ""

    def _extract_poi_name_from_text(self, item: dict[str, Any], fallback_title: str) -> str:
        for key in ("poi_name", "poi", "name", "spot_name", "attraction_name", "location_name"):
            value = str(item.get(key) or "").strip()
            if value:
                return value
        return fallback_title

    def _load_notes_from_file(self, path: Path, *, default_origin: str) -> list[dict[str, Any]]:
        try:
            payload = self._read_json_file(path)
        except Exception:
            return []
        try:
            normalized, _ = self._adapt_import_payload(payload, default_origin=default_origin, format_hint="auto")
            return [self._normalize_note(item, default_origin=default_origin) for item in normalized if isinstance(item, dict)]
        except Exception:
            return []

    def _load_runtime_import_candidates(self) -> list[dict[str, Any]]:
        if not self.runtime_notes_path.exists():
            return []
        return self._load_notes_from_file(self.runtime_notes_path, default_origin="external")

    def _load_external_candidates(self) -> list[dict[str, Any]]:
        imported_notes = self._load_runtime_import_candidates()
        if imported_notes:
            return imported_notes

        sample_path = (self.settings.xhs_sample_notes_path or "").strip()
        if not sample_path:
            return []
        return self._load_notes_from_file(Path(sample_path), default_origin="external")

    def _normalize_note(self, item: dict[str, Any], *, default_origin: str) -> dict[str, Any]:
        title = str(item.get("title") or item.get("poi_name") or item.get("city") or "旅行内容").strip()
        poi_name = str(item.get("poi_name") or item.get("poi") or "").strip()
        city = str(item.get("city") or "").strip()

        raw_images = item.get("images")
        images = self._normalize_image_list(raw_images, default_alt=title)

        return {
            "id": str(item.get("id") or f"xhs-{city or 'unknown'}-{poi_name or title}").strip(),
            "source_type": "xhs",
            "source_label": str(item.get("source_label") or "小红书公开内容").strip(),
            "origin": str(item.get("origin") or default_origin).strip() or default_origin,
            "title": title,
            "city": city,
            "poi_name": poi_name,
            "author": str(item.get("author") or "").strip(),
            "tags": self._normalize_text_list(item.get("tags")),
            "images": images,
            "highlights": self._normalize_text_list(item.get("highlights")),
            "cautions": self._normalize_text_list(item.get("cautions")),
            "excerpt": str(item.get("excerpt") or "").strip(),
            "match_reason": str(item.get("match_reason") or "").strip(),
            "note_url": str(item.get("note_url") or "").strip(),
        }

    def _build_normalized_external_note(
        self,
        *,
        title: str,
        city: str,
        poi_name: str,
        author: str,
        tags: list[str],
        images: list[dict[str, str]],
        highlights: list[str],
        cautions: list[str],
        excerpt: str,
        match_reason: str,
        note_url: str,
        note_id: str,
        source_label: str,
        default_origin: str,
    ) -> dict[str, Any]:
        return self._normalize_note(
            {
                "id": note_id or f"xhs-{city or 'unknown'}-{poi_name or title}",
                "source_type": "xhs",
                "source_label": source_label,
                "origin": default_origin,
                "title": title,
                "city": city,
                "poi_name": poi_name,
                "author": author,
                "tags": tags,
                "images": images,
                "highlights": highlights,
                "cautions": cautions,
                "excerpt": excerpt,
                "match_reason": match_reason,
                "note_url": note_url,
            },
            default_origin=default_origin,
        )

    def _extract_note_from_search_item(
        self,
        item: dict[str, Any],
        *,
        default_origin: str,
        context: dict[str, Any],
        detail_lookup: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else item
        title = str(note_card.get("display_title") or note_card.get("title") or item.get("title") or "").strip()
        if not title:
            return None

        note_id = str(item.get("id") or note_card.get("note_id") or note_card.get("id") or "").strip()
        detail_note = (detail_lookup or {}).get(note_id, {})
        detail_card = detail_note.get("note_card") if isinstance(detail_note.get("note_card"), dict) else detail_note

        city = self._extract_city_from_text(detail_card or note_card, context)
        author = str(
            (note_card.get("user") or {}).get("nickname")
            or (detail_card.get("user") or {}).get("nickname")
            or item.get("author")
            or ""
        ).strip()
        poi_name = self._extract_poi_name_from_text(detail_card or note_card, title)
        tags = self._normalize_text_list(
            note_card.get("tag_list")
            or note_card.get("tags")
            or detail_card.get("tag_list")
            or detail_card.get("tags")
        )
        cover = note_card.get("cover") or detail_card.get("cover") or {}
        image_sources = note_card.get("image_list") or detail_card.get("image_list") or cover
        images = self._normalize_image_list(image_sources, default_alt=title)

        desc = str(detail_card.get("desc") or note_card.get("desc") or item.get("desc") or "").strip()
        highlights = self._normalize_text_list(item.get("highlights"))
        if desc and not highlights:
            highlights = [desc[:120]]
        cautions = self._normalize_text_list(item.get("cautions"))

        return self._build_normalized_external_note(
            title=title,
            city=city,
            poi_name=poi_name,
            author=author,
            tags=tags,
            images=images,
            highlights=highlights,
            cautions=cautions,
            excerpt=desc or title,
            match_reason=str(item.get("match_reason") or "来自小红书搜索结果的原始笔记内容").strip(),
            note_url=str(item.get("note_url") or "").strip(),
            note_id=note_id,
            source_label="小红书原始搜索结果",
            default_origin=default_origin,
        )

    def _extract_note_from_detail_item(
        self,
        item: dict[str, Any],
        *,
        default_origin: str,
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else item
        title = str(note_card.get("display_title") or note_card.get("title") or "").strip()
        desc = str(note_card.get("desc") or "").strip()
        if not title and not desc:
            return None

        title = title or desc[:24] or "旅行内容"
        city = self._extract_city_from_text(note_card, context)
        poi_name = self._extract_poi_name_from_text(note_card, title)
        author = str((note_card.get("user") or {}).get("nickname") or note_card.get("author") or "").strip()
        tags = self._normalize_text_list(note_card.get("tag_list") or note_card.get("tags"))
        images = self._normalize_image_list(note_card.get("image_list") or note_card.get("cover"), default_alt=title)

        return self._build_normalized_external_note(
            title=title,
            city=city,
            poi_name=poi_name,
            author=author,
            tags=tags,
            images=images,
            highlights=[desc[:120]] if desc else [],
            cautions=self._normalize_text_list(note_card.get("cautions")),
            excerpt=desc or title,
            match_reason="来自小红书详情结果的原始笔记内容",
            note_url=str(note_card.get("note_url") or "").strip(),
            note_id=str(note_card.get("note_id") or note_card.get("id") or "").strip(),
            source_label="小红书详情结果",
            default_origin=default_origin,
        )

    def _extract_note_from_generic_item(
        self,
        item: dict[str, Any],
        *,
        default_origin: str,
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        title = str(item.get("title") or item.get("name") or item.get("headline") or "").strip()
        content = str(item.get("content") or item.get("desc") or item.get("excerpt") or item.get("summary") or "").strip()
        city = self._extract_city_from_text(item, context)
        if not title and not content:
            return None

        title = title or content[:24] or "旅行内容"
        poi_name = self._extract_poi_name_from_text(item, title)
        images = self._normalize_image_list(item.get("images") or item.get("photos") or item.get("image"), default_alt=title)
        tags = self._normalize_text_list(item.get("tags") or item.get("topics") or item.get("labels"))
        highlights = self._normalize_text_list(item.get("highlights"))
        if content and not highlights:
            highlights = [content[:120]]

        source_label = str(item.get("source_label") or context.get("source_label") or "第三方中间内容").strip()
        return self._build_normalized_external_note(
            title=title,
            city=city,
            poi_name=poi_name,
            author=str(item.get("author") or item.get("nickname") or "").strip(),
            tags=tags,
            images=images,
            highlights=highlights,
            cautions=self._normalize_text_list(item.get("cautions") or item.get("tips")),
            excerpt=content or title,
            match_reason=str(item.get("match_reason") or context.get("match_reason") or "来自第三方中间结果的内容适配").strip(),
            note_url=str(item.get("note_url") or item.get("url") or "").strip(),
            note_id=str(item.get("id") or item.get("note_id") or "").strip(),
            source_label=source_label,
            default_origin=default_origin,
        )

    def _build_detail_lookup(self, payload: Any) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        if isinstance(payload, dict):
            note_card = payload.get("note_card") if isinstance(payload.get("note_card"), dict) else payload
            note_id = str(note_card.get("note_id") or note_card.get("id") or payload.get("id") or "").strip()
            if note_id:
                lookup[note_id] = payload

            items = payload.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        note_card = item.get("note_card") if isinstance(item.get("note_card"), dict) else item
                        note_id = str(note_card.get("note_id") or note_card.get("id") or item.get("id") or "").strip()
                        if note_id:
                            lookup[note_id] = item
            for value in payload.values():
                if isinstance(value, dict):
                    lookup.update(self._build_detail_lookup(value))
                elif isinstance(value, list):
                    for child in value:
                        if isinstance(child, dict):
                            lookup.update(self._build_detail_lookup(child))
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    lookup.update(self._build_detail_lookup(item))
        return lookup

    def _adapt_import_payload(
        self,
        payload: Any,
        *,
        default_origin: str,
        format_hint: str = "auto",
        context: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        context = context or {}
        hint = (format_hint or "auto").strip().lower()

        if isinstance(payload, list):
            if not payload:
                return [], hint or "empty_list"
            first = payload[0] if isinstance(payload[0], dict) else {}
            if hint == "third_party_items":
                notes = [
                    note
                    for item in payload
                    if isinstance(item, dict)
                    for note in [self._extract_note_from_generic_item(item, default_origin=default_origin, context=context)]
                    if note
                ]
                return notes, "third_party_items"
            if hint == "normalized_notes" or (hint == "auto" and "title" in first and "city" in first and "poi_name" in first):
                return [self._normalize_note(item, default_origin=default_origin) for item in payload if isinstance(item, dict)], "normalized_notes"
            if hint in {"xhs_search_items", "xhs_search_response"} or first.get("model_type") == "note" or "note_card" in first:
                detail_lookup = self._build_detail_lookup(context.get("detail_payload"))
                notes = [
                    note
                    for item in payload
                    if isinstance(item, dict)
                    for note in [self._extract_note_from_search_item(item, default_origin=default_origin, context=context, detail_lookup=detail_lookup)]
                    if note
                ]
                return notes, "xhs_search_items"
            notes = [
                note
                for item in payload
                if isinstance(item, dict)
                for note in [self._extract_note_from_generic_item(item, default_origin=default_origin, context=context)]
                if note
            ]
            return notes, "third_party_items"

        if not isinstance(payload, dict):
            raise ValueError("导入内容必须是 JSON 对象或数组")

        if "notes" in payload and isinstance(payload.get("notes"), list):
            return self._adapt_import_payload(
                payload.get("notes"),
                default_origin=default_origin,
                format_hint="normalized_notes" if hint == "auto" else hint,
                context={**context, **payload},
            )

        if "items" in payload and isinstance(payload.get("items"), list):
            return self._adapt_import_payload(
                payload.get("items"),
                default_origin=default_origin,
                format_hint="third_party_items" if hint == "auto" else hint,
                context={**context, **payload},
            )

        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            items = data.get("items") or []
            if items and isinstance(items[0], dict) and items[0].get("model_type") == "note":
                detail_payload = (
                    payload.get("detail_response")
                    or payload.get("detail_payload")
                    or payload.get("detail_responses")
                    or context.get("detail_payload")
                    or {}
                )
                return self._adapt_import_payload(
                    items,
                    default_origin=default_origin,
                    format_hint="xhs_search_items",
                    context={**context, **payload, "detail_payload": detail_payload},
                )
            notes = [
                note
                for item in items
                if isinstance(item, dict)
                for note in [self._extract_note_from_detail_item(item, default_origin=default_origin, context={**context, **payload})]
                if note
            ]
            return notes, "xhs_detail_response"

        if "search_response" in payload:
            detail_payload = payload.get("detail_response") or payload.get("detail_responses") or {}
            return self._adapt_import_payload(
                payload.get("search_response"),
                default_origin=default_origin,
                format_hint="xhs_search_response",
                context={**context, **payload, "detail_payload": detail_payload},
            )

        if "detail_response" in payload:
            return self._adapt_import_payload(
                payload.get("detail_response"),
                default_origin=default_origin,
                format_hint="xhs_detail_response",
                context={**context, **payload},
            )

        note = self._extract_note_from_generic_item(payload, default_origin=default_origin, context=context)
        return ([note] if note else []), "single_third_party_item"

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

    def validate_import_payload(self, payload: Any, *, format_hint: str = "auto") -> tuple[list[dict[str, Any]], str]:
        normalized, detected_format = self._adapt_import_payload(payload, default_origin="external", format_hint=format_hint)
        if not normalized:
            raise ValueError("未能从当前 JSON 中识别出可用的小红书内容，请检查是否为 TripStar 搜索结果、详情结果或第三方中间数据")

        validated: list[dict[str, Any]] = []
        for index, item in enumerate(normalized):
            normalized_note = self._normalize_note(item, default_origin="external")
            if not normalized_note.get("city"):
                raise ValueError(f"第 {index + 1} 条内容缺少 city")
            if not normalized_note.get("title"):
                raise ValueError(f"第 {index + 1} 条内容缺少 title")
            validated.append(normalized_note)

        return validated, detected_format

    def import_notes(self, payload: Any, *, source_name: str = "", format_hint: str = "auto") -> dict[str, Any]:
        normalized, detected_format = self.validate_import_payload(payload, format_hint=format_hint)
        self.runtime_notes_path.parent.mkdir(parents=True, exist_ok=True)
        self.runtime_notes_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")

        metadata = {
            "source_name": source_name.strip() or "uploaded_notes.json",
            "note_count": len(normalized),
            "format_kind": detected_format,
            "updated_at": datetime.now(UTC).isoformat(),
            "path": str(self.runtime_notes_path),
            "active_source": "runtime_import",
        }
        self.runtime_meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.get_content_source_status()

    def clear_imported_notes(self) -> dict[str, Any]:
        if self.runtime_notes_path.exists():
            self.runtime_notes_path.unlink()
        if self.runtime_meta_path.exists():
            self.runtime_meta_path.unlink()
        return self.get_content_source_status()

    def get_content_source_status(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self.runtime_meta_path.exists():
            try:
                loaded = self._read_json_file(self.runtime_meta_path)
                if isinstance(loaded, dict):
                    metadata = loaded
            except Exception:
                metadata = {}

        if self.runtime_notes_path.exists():
            note_count = len(self._load_runtime_import_candidates())
            return {
                "active_source": "runtime_import",
                "source_name": metadata.get("source_name") or self.runtime_notes_path.name,
                "path": str(self.runtime_notes_path),
                "note_count": note_count,
                "format_kind": metadata.get("format_kind") or "normalized_notes",
                "updated_at": metadata.get("updated_at") or "",
                "uses_builtin_fallback": False,
            }

        sample_path = (self.settings.xhs_sample_notes_path or "").strip()
        if sample_path:
            note_count = len(self._load_notes_from_file(Path(sample_path), default_origin="external"))
            return {
                "active_source": "configured_path",
                "source_name": Path(sample_path).name,
                "path": sample_path,
                "note_count": note_count,
                "format_kind": "configured_path",
                "updated_at": "",
                "uses_builtin_fallback": note_count == 0,
            }

        return {
            "active_source": "builtin_fallback",
            "source_name": "builtin_xhs_notes",
            "path": "",
            "note_count": len(BUILTIN_XHS_NOTES),
            "format_kind": "builtin_fallback",
            "updated_at": "",
            "uses_builtin_fallback": True,
        }

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
