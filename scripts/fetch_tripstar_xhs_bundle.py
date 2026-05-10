"""Helper script: fetch TripStar XHS search/detail data in an isolated process."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


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
    cookie = str(payload.get("cookie") or "").strip()
    max_items = max(1, min(int(payload.get("max_items") or 4), 8))

    if not city:
        _emit({"success": False, "message": "city 不能为空"})
        return 1
    if not cookie:
        _emit({"success": False, "message": "cookie 不能为空"})
        return 1

    query = f"{city} {keywords} 旅游 景点攻略".strip()
    client = XhsNativeClient(cookie)

    try:
        search_response = client.search_notes(keyword=query, page_size=max_items)
    except Exception as exc:
        _emit({"success": False, "message": f"TripStar 搜索失败: {exc}"})
        return 1

    items = search_response.get("data", {}).get("items", [])
    detail_items: list[dict] = []
    matched_count = 0
    for item in items:
        if not isinstance(item, dict) or item.get("model_type") != "note":
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
                "keywords": keywords,
                "search_response": search_response,
                "detail_response": {"data": {"items": detail_items}},
            },
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
