"""Runtime XHS live-fetch bridge using TripStar as an isolated helper."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.xhs_content_service import XHSContentService


class XHSLiveFetchError(RuntimeError):
    """Raised when the live XHS fetch bridge cannot refresh content."""

    def __init__(self, message: str, *, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.detail = detail or {}


class XHSLiveFetchService:
    """Bridge live fetch requests to TripStar without importing its app package inline."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.content_service = XHSContentService()
        self.project_root = Path(__file__).resolve().parents[3]
        self.helper_script = self.project_root / "TravelAgentSystem" / "scripts" / "fetch_tripstar_xhs_bundle.py"
        self.debug_dir = self.project_root / "TravelAgentSystem" / "logs" / "xhs_debug"
        self.latest_debug_file = self.debug_dir / "latest.json"

    def _write_debug_log(self, payload: dict[str, Any]) -> None:
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        payload = {
            "logged_at": datetime.now(UTC).isoformat(),
            **payload,
        }
        log_file = self.debug_dir / f"{timestamp}.json"
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        log_file.write_text(serialized, encoding="utf-8")
        self.latest_debug_file.write_text(serialized, encoding="utf-8")

    def get_latest_debug_log(self) -> dict[str, Any]:
        if not self.latest_debug_file.exists():
            return {}
        try:
            return json.loads(self.latest_debug_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

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
        cookie_diagnostics = self.content_service.get_xhs_cookie_diagnostics(normalized_cookie)
        if not cookie_diagnostics.get("has_minimum_required"):
            missing = "、".join(cookie_diagnostics.get("missing_required") or [])
            raise XHSLiveFetchError(
                f"当前小红书 Cookie 不完整，缺少关键字段：{missing}。请粘贴浏览器请求里的完整 Cookie Header，而不是单独某一个 cookie。",
                detail={
                    "cookie_key_count": cookie_diagnostics.get("cookie_key_count", 0),
                    "cookie_keys": cookie_diagnostics.get("cookie_keys", []),
                    "missing_required": cookie_diagnostics.get("missing_required", []),
                    "missing_recommended": cookie_diagnostics.get("missing_recommended", []),
                },
            )

        payload = {
            "city": city.strip(),
            "keywords": keywords.strip(),
            "poi_names": [str(item).strip() for item in (poi_names or []) if str(item).strip()][:4],
            "max_items": max(1, min(int(max_items or 4), 8)),
            "cookie": normalized_cookie,
            "rap_param": str(self.settings.xhs_rap_param or "").strip(),
            "project_root": str(self.project_root),
        }
        masked_payload = {
            **payload,
            "cookie": f"<masked:{len(normalized_cookie)} chars>",
            "cookie_diagnostics": cookie_diagnostics,
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
            self._write_debug_log(
                {
                    "phase": "timeout",
                    "request": masked_payload,
                    "message": "调用 TripStar 小红书实时刷新超时，请稍后重试。",
                }
            )
            raise XHSLiveFetchError("调用 TripStar 小红书实时刷新超时，请稍后重试。") from exc

        raw_output = (result.stdout or "").strip()
        debug_payload: dict[str, Any] = {
            "phase": "completed",
            "request": masked_payload,
            "returncode": result.returncode,
            "stdout_preview": raw_output[:4000],
            "stderr_preview": (result.stderr or "").strip()[:4000],
        }
        if result.returncode != 0 and not raw_output:
            message = (result.stderr or "").strip() or "TripStar helper 运行失败。"
            self._write_debug_log(
                {
                    **debug_payload,
                    "success": False,
                    "message": message,
                }
            )
            raise XHSLiveFetchError(message, detail={"stderr": message})

        response = self._extract_json_from_output(raw_output)
        debug_payload["parsed_response_summary"] = {
            "success": response.get("success"),
            "message": response.get("message"),
            "query": response.get("query"),
            "raw_note_count": response.get("raw_note_count"),
            "query_candidates": (response.get("data") or {}).get("query_candidates"),
            "request_debug": (response.get("data") or {}).get("request_debug"),
            "search_item_count": (response.get("data") or {}).get("search_item_count"),
            "search_model_types": (response.get("data") or {}).get("search_model_types"),
            "search_item_preview": (response.get("data") or {}).get("search_item_preview"),
        }

        if not response.get("success"):
            self._write_debug_log(
                {
                    **debug_payload,
                    "success": False,
                    "message": str(response.get("message") or "TripStar 实时抓取失败。"),
                }
            )
            raise XHSLiveFetchError(
                str(response.get("message") or "TripStar 实时抓取失败。"),
                detail=response if isinstance(response, dict) else {},
            )

        bundle = response.get("data")
        if not bundle:
            self._write_debug_log(
                {
                    **debug_payload,
                    "success": False,
                    "message": "TripStar 实时抓取没有返回可用数据。",
                }
            )
            raise XHSLiveFetchError("TripStar 实时抓取没有返回可用数据。", detail=response)

        raw_note_count = int(response.get("raw_note_count") or 0)
        if raw_note_count <= 0:
            tried_queries = response.get("data", {}).get("query_candidates") or []
            query_hint = "；".join(str(item) for item in tried_queries[:3] if str(item).strip())
            item_count = int(response.get("data", {}).get("search_item_count") or 0)
            model_types = response.get("data", {}).get("search_model_types") or []
            model_hint = "、".join(str(item) for item in model_types[:5] if str(item).strip())
            message = (
                f"已发起小红书实时搜索，但当前查询 `{response.get('query') or city}` 没有返回可用笔记。"
                + (f" 本次已尝试：{query_hint}。" if query_hint else "")
                + (f" 搜索响应共返回 {item_count} 条 items。" if item_count else "")
                + (f" 顶部 model_type: {model_hint}。" if model_hint else "")
                + " 你可以改用更短的城市词、补充更贴近景点的关键词，或稍后重试。"
            )
            self._write_debug_log(
                {
                    **debug_payload,
                    "success": False,
                    "message": message,
                }
            )
            raise XHSLiveFetchError(
                message,
                detail={
                    "query": response.get("query") or city,
                    "query_candidates": tried_queries,
                    "raw_note_count": raw_note_count,
                    "search_item_count": item_count,
                    "search_model_types": model_types,
                    "search_item_preview": response.get("data", {}).get("search_item_preview") or [],
                },
            )

        try:
            status = self.content_service.import_notes(
                bundle,
                source_name=f"tripstar-live-{city.strip() or 'xhs'}.json",
                format_hint="xhs_search_response",
            )
        except ValueError as exc:
            self._write_debug_log(
                {
                    **debug_payload,
                    "success": False,
                    "message": f"小红书实时抓取已返回响应，但内容适配失败：{exc}",
                }
            )
            raise XHSLiveFetchError(
                f"小红书实时抓取已返回响应，但内容适配失败：{exc}",
                detail={
                    "query": response.get("query") or city,
                    "raw_note_count": raw_note_count,
                },
            ) from exc

        success_payload = {
            "status": status,
            "query": response.get("query") or "",
            "raw_note_count": raw_note_count,
        }
        self._write_debug_log(
            {
                **debug_payload,
                "success": True,
                "message": "TripStar 实时抓取成功并已导入运行时内容源。",
                "result": success_payload,
            }
        )
        return success_payload
