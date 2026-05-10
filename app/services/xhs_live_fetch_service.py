"""Runtime XHS live-fetch bridge using TripStar as an isolated helper."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.xhs_content_service import XHSContentService


class XHSLiveFetchError(RuntimeError):
    """Raised when the live XHS fetch bridge cannot refresh content."""


class XHSLiveFetchService:
    """Bridge live fetch requests to TripStar without importing its app package inline."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.content_service = XHSContentService()
        self.project_root = Path(__file__).resolve().parents[3]
        self.helper_script = self.project_root / "TravelAgentSystem" / "scripts" / "fetch_tripstar_xhs_bundle.py"

    def _extract_json_from_output(self, raw_output: str) -> dict[str, Any]:
        content = (raw_output or "").strip()
        if not content:
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        first_brace = content.find("{")
        last_brace = content.rfind("}")
        if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
            raise XHSLiveFetchError(f"TripStar helper 返回了不可解析内容：{content[:200]}")

        candidate = content[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise XHSLiveFetchError(f"TripStar helper 返回了不可解析内容：{content[:200]}") from exc

    def refresh_from_tripstar(
        self,
        *,
        city: str,
        keywords: str = "",
        poi_names: list[str] | None = None,
        max_items: int = 4,
    ) -> dict[str, Any]:
        normalized_cookie = self.content_service.normalize_xhs_cookie(self.settings.xhs_cookie)
        if not normalized_cookie:
            raise XHSLiveFetchError("当前未配置小红书 Cookie，无法进行实时内容刷新。")

        payload = {
            "city": city.strip(),
            "keywords": keywords.strip(),
            "poi_names": [str(item).strip() for item in (poi_names or []) if str(item).strip()][:4],
            "max_items": max(1, min(int(max_items or 4), 8)),
            "cookie": normalized_cookie,
            "project_root": str(self.project_root),
        }

        try:
            result = subprocess.run(
                [sys.executable, str(self.helper_script)],
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=45,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise XHSLiveFetchError("调用 TripStar 小红书实时刷新超时，请稍后重试。") from exc

        raw_output = (result.stdout or "").strip()
        if result.returncode != 0 and not raw_output:
            message = (result.stderr or "").strip() or "TripStar helper 运行失败。"
            raise XHSLiveFetchError(message)

        response = self._extract_json_from_output(raw_output)

        if not response.get("success"):
            raise XHSLiveFetchError(str(response.get("message") or "TripStar 实时抓取失败。"))

        bundle = response.get("data")
        if not bundle:
            raise XHSLiveFetchError("TripStar 实时抓取没有返回可用数据。")

        raw_note_count = int(response.get("raw_note_count") or 0)
        if raw_note_count <= 0:
            tried_queries = response.get("data", {}).get("query_candidates") or []
            query_hint = "；".join(str(item) for item in tried_queries[:3] if str(item).strip())
            raise XHSLiveFetchError(
                f"已发起小红书实时搜索，但当前查询 `{response.get('query') or city}` 没有返回可用笔记。"
                + (f" 本次已尝试：{query_hint}。" if query_hint else "")
                + " 你可以改用更短的城市词、补充更贴近景点的关键词，或稍后重试。"
            )

        try:
            status = self.content_service.import_notes(
                bundle,
                source_name=f"tripstar-live-{city.strip() or 'xhs'}.json",
                format_hint="xhs_search_response",
            )
        except ValueError as exc:
            raise XHSLiveFetchError(f"小红书实时抓取已返回响应，但内容适配失败：{exc}") from exc

        return {
            "status": status,
            "query": response.get("query") or "",
            "raw_note_count": raw_note_count,
        }
