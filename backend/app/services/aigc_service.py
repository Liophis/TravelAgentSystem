from typing import Any


def generate_diary_draft(payload: dict[str, Any]) -> dict[str, Any]:
    topic = payload.get("topic") or "沙河校区游览"
    keywords = _normalize_keywords(payload.get("keywords"))
    tone = payload.get("tone") or "自然"
    keyword_text = "、".join(keywords) if keywords else "路线、设施、校园体验"
    title = f"{topic}：{keyword_text.split('、')[0]}体验"
    draft = (
        f"今天围绕{topic}完成了一次校园导览体验。"
        f"这次重点关注{keyword_text}，整体感受是路线清晰、信息集中，"
        f"适合用{tone}的语气整理成游记发布。"
    )
    prompt = (
        "请根据以下信息生成一篇中文旅游/校园游记："
        f"主题={topic}；关键词={keyword_text}；语气={tone}；"
        "要求包含路线体验、设施观察和个人感受。"
    )
    return {
        "title": title,
        "draft": draft,
        "prompt": prompt,
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "mode": "mock AIGC deterministic template",
            "keywords": str(len(keywords)),
        },
    }


def generate_storyboard(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text") or "沙河校区一日游"
    scene_count = min(max(int(payload.get("scene_count") or 4), 1), 8)
    scenes = [
        {
            "index": index,
            "title": f"镜头 {index}",
            "description": _scene_description(text, index),
            "duration_seconds": 5 + index,
        }
        for index in range(1, scene_count + 1)
    ]
    prompt = (
        f"请把以下文本改写成 {scene_count} 个短视频分镜，"
        "每个分镜包含画面、字幕和转场建议："
        f"{text}"
    )
    return {
        "scenes": scenes,
        "prompt": prompt,
        "simulated_video_url": "https://example.local/aigc/storyboards/mock-campus-tour.mp4",
        "algorithm_trace": {
            "stage": "stage-9-food-aigc-admin",
            "mode": "mock AIGC storyboard generator",
            "scene_count": str(scene_count),
        },
    }


def _normalize_keywords(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _scene_description(text: str, index: int) -> str:
    themes = ["校门出发", "沿路导览", "设施特写", "美食停留", "总结回望", "地图路线", "互动评论", "发布游记"]
    theme = themes[(index - 1) % len(themes)]
    return f"{theme}：结合“{text[:32]}”展示校园游览亮点。"
