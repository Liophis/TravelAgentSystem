"""Trip chat service - answers questions from the current trip plan context."""

from __future__ import annotations

from collections import Counter


def _extract_days(trip_plan: dict) -> list[dict]:
    days = trip_plan.get("days")
    return days if isinstance(days, list) else []


def _extract_attractions(trip_plan: dict) -> list[dict]:
    attractions: list[dict] = []
    for day in _extract_days(trip_plan):
        day_attractions = day.get("attractions")
        if isinstance(day_attractions, list):
            attractions.extend(item for item in day_attractions if isinstance(item, dict))
    return attractions


def _format_budget(trip_plan: dict) -> str | None:
    budget = trip_plan.get("budget")
    if not isinstance(budget, dict):
        return None

    total = budget.get("total")
    attractions = budget.get("total_attractions")
    hotels = budget.get("total_hotels")
    meals = budget.get("total_meals")
    transportation = budget.get("total_transportation")

    if total is None:
        return None

    return (
        f"当前预算合计约为 {total}。"
        f" 其中景点 {attractions or 0}、住宿 {hotels or 0}、餐饮 {meals or 0}、交通 {transportation or 0}。"
    )


def _format_overview(trip_plan: dict) -> str:
    city = trip_plan.get("city") or "当前城市"
    start_date = trip_plan.get("start_date") or "未提供开始日期"
    end_date = trip_plan.get("end_date") or "未提供结束日期"
    days = _extract_days(trip_plan)
    attractions = _extract_attractions(trip_plan)
    return (
        f"这是一份 {city} 的行程，从 {start_date} 到 {end_date}，"
        f"共 {len(days)} 天，当前安排了 {len(attractions)} 个景点。"
    )


def _format_day_summary(trip_plan: dict) -> str:
    days = _extract_days(trip_plan)
    if not days:
        return "当前行程里还没有可总结的每日安排。"

    lines: list[str] = []
    for day in days:
        day_index = int(day.get("day_index", 0)) + 1
        description = day.get("description") or "暂无说明"
        attractions = day.get("attractions") or []
        attraction_names = [item.get("name") for item in attractions if isinstance(item, dict) and item.get("name")]
        if attraction_names:
            lines.append(f"第 {day_index} 天：{description}。景点包括：{'、'.join(attraction_names[:4])}。")
        else:
            lines.append(f"第 {day_index} 天：{description}。")
    return " ".join(lines)


def _format_attraction_summary(trip_plan: dict) -> str:
    attractions = _extract_attractions(trip_plan)
    if not attractions:
        return "当前行程里还没有景点数据。"

    names = [item.get("name") for item in attractions if item.get("name")]
    counts = Counter(names)
    unique_names = list(counts.keys())[:8]
    return f"当前行程涉及这些景点：{'、'.join(unique_names)}。"


def answer_trip_question(message: str, trip_plan: dict, history: list[dict] | None = None) -> str:
    """Answer a trip-related question from the current plan with simple heuristics."""
    normalized = (message or "").strip().lower()
    if not trip_plan:
        return "我还没有拿到当前行程数据，所以暂时不能回答具体问题。请先生成行程。"

    budget_keywords = ("预算", "花费", "费用", "多少钱", "cost", "budget", "price")
    day_keywords = ("每天", "日程", "安排", "day", "schedule", "itinerary")
    attraction_keywords = ("景点", "去哪", "attraction", "poi", "spot")
    suggest_keywords = ("建议", "适合", "recommend", "suitable", "tips")

    parts = [_format_overview(trip_plan)]

    if any(keyword in normalized for keyword in budget_keywords):
        budget_text = _format_budget(trip_plan)
        if budget_text:
            parts.append(budget_text)
        else:
            parts.append("当前计划里还没有完整预算，我建议下一步先补齐预算估算逻辑。")
    elif any(keyword in normalized for keyword in day_keywords):
        parts.append(_format_day_summary(trip_plan))
    elif any(keyword in normalized for keyword in attraction_keywords):
        parts.append(_format_attraction_summary(trip_plan))
    elif any(keyword in normalized for keyword in suggest_keywords):
        suggestion = trip_plan.get("overall_suggestions") or "当前计划已经生成，但建议说明还比较简略。"
        parts.append(f"结合当前计划，我的建议是：{suggestion}")
    else:
        suggestion = trip_plan.get("overall_suggestions")
        if suggestion:
            parts.append(f"当前行程建议：{suggestion}")
        parts.append("如果你愿意，我可以继续按预算、每日安排、景点选择这几个方向继续细化回答。")

    return " ".join(part.strip() for part in parts if part.strip())
