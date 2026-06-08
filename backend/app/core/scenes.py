from typing import Any

DEFAULT_SCENE_KEY = "bupt_shahe"
SUMMER_PALACE_SCENE_KEY = "summer_palace"

SCENES: dict[str, dict[str, Any]] = {
    DEFAULT_SCENE_KEY: {
        "key": DEFAULT_SCENE_KEY,
        "display_name": "北京邮电大学沙河校区",
        "scope": "campus",
        "center": [116.28333, 40.15608],
    },
    SUMMER_PALACE_SCENE_KEY: {
        "key": SUMMER_PALACE_SCENE_KEY,
        "display_name": "北京颐和园",
        "scope": "scenic",
        "center": [116.2755, 39.9996],
    },
}


def normalize_scene_key(scene_key: Any) -> str:
    if isinstance(scene_key, str) and scene_key in SCENES:
        return scene_key
    return DEFAULT_SCENE_KEY


def scene_center(scene_key: str | None) -> list[float]:
    return list(SCENES[normalize_scene_key(scene_key)]["center"])


def scene_display_name(scene_key: str | None) -> str:
    return str(SCENES[normalize_scene_key(scene_key)]["display_name"])
