"""高德地图实时POI搜索服务 - 支持全国美食推荐"""

import httpx
from typing import Any

from app.core.config import settings

# 高德周边搜索API配置
AMAP_PLACE_AROUND_URL = "https://restapi.amap.com/v3/place/around"
# 餐饮服务类型代码
AMAP_FOOD_TYPES = "050000"  # 餐饮


class AmapPoiError(Exception):
    """高德POI搜索错误"""
    pass


async def search_nearby_restaurants(
    lng: float,
    lat: float,
    radius: int = 3000,
    keyword: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    使用高德周边搜索API获取附近餐厅

    Args:
        lng: 经度 (WGS84)
        lat: 纬度 (WGS84)
        radius: 搜索半径(米)，默认3000
        keyword: 关键词(可选)
        limit: 返回数量，默认20

    Returns:
        格式化的餐厅列表
    """
    if not settings.amap_web_api_key:
        raise AmapPoiError("AMAP_WEB_API_KEY not configured")

    # 高德API使用GCJ02坐标，需要转换
    from app.services.coordinate_utils import wgs84_to_gcj02
    gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)

    params = {
        "key": settings.amap_web_api_key,
        "location": f"{gcj_lng},{gcj_lat}",
        "radius": radius,
        "types": AMAP_FOOD_TYPES,
        "offset": min(limit, 25),  # 高德最大返回25条
        "page": 1,
        "extensions": "all",  # 获取详细信息
    }

    if keyword:
        params["keywords"] = keyword

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(AMAP_PLACE_AROUND_URL, params=params)
        data = response.json()

    if data.get("status") != "1":
        error_msg = data.get("info", "Unknown error")
        raise AmapPoiError(f"Amap API error: {error_msg}")

    pois = data.get("pois", [])
    restaurants = [_format_poi_to_restaurant(poi) for poi in pois]

    return {
        "items": restaurants,
        "total": len(restaurants),
        "center": {"lng": lng, "lat": lat},
        "radius": radius,
        "source": "amap_realtime",
        "algorithm_trace": {
            "source": "amap_place_around_api",
            "coordinate": f"{lng},{lat}",
            "radius": radius,
            "raw_count": len(pois),
        },
    }


def _format_poi_to_restaurant(poi: dict) -> dict[str, Any]:
    """将高德POI格式化为系统餐厅格式"""
    # 解析位置（高德返回的是GCJ02，需要转为WGS84）
    from app.services.coordinate_utils import gcj02_to_wgs84

    location = poi.get("location", "0,0")
    gcj_lng, gcj_lat = map(float, location.split(","))
    wgs_lng, wgs_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)

    # 解析价格（如果有）
    price_text = poi.get("biz_ext", {}).get("price", "0")
    try:
        price = float(price_text) if price_text else 0.0
    except ValueError:
        price = 0.0

    # 解析评分
    rating_text = poi.get("biz_ext", {}).get("rating", "4.0")
    try:
        rating = float(rating_text) if rating_text else 4.0
    except ValueError:
        rating = 4.0

    # 构建餐厅数据
    return {
        "id": f"amap_{poi.get('id', 'unknown')}",
        "name": poi.get("name", "未知餐厅"),
        "lng": wgs_lng,
        "lat": wgs_lat,
        "address": poi.get("address", ""),
        "category": poi.get("type", "餐饮"),
        "tel": poi.get("tel", ""),
        "rating": min(rating, 5.0),
        "price": price,
        "heat": int(float(poi.get("biz_ext", {}).get("cost", "0") or 0)),
        "source": "amap_realtime",
        "external_id": poi.get("id", ""),
        "photos": poi.get("photos", []),
        "distance": int(float(poi.get("distance", 0) or 0)),  # 距离(米)
    }


async def search_foods_at_location(
    lng: float,
    lat: float,
    cuisine: str | None = None,
    radius: int = 3000,
    limit: int = 20,
) -> dict[str, Any]:
    """
    在指定位置搜索美食（模拟Food结构）

    由于高德返回的是餐厅POI，我们需要将其转换为系统的美食格式
    每个餐厅生成几道代表性菜品
    """
    result = await search_nearby_restaurants(lng, lat, radius, None, limit)
    restaurants = result["items"]

    # 将餐厅转换为美食项（每个餐厅生成1-3道菜品）
    foods = []
    for restaurant in restaurants:
        # 根据餐厅类型生成菜品
        cuisine_type = _guess_cuisine_type(restaurant["category"], restaurant["name"])

        # 生成2道代表性菜品
        for i, food_name in enumerate(_generate_food_names(restaurant["name"], cuisine_type)):
            foods.append({
                "id": f"{restaurant['id']}_food_{i}",
                "restaurant_id": restaurant["id"],
                "restaurant_name": restaurant["name"],
                "restaurant_lng": restaurant["lng"],
                "restaurant_lat": restaurant["lat"],
                "restaurant_address": restaurant["address"],
                "restaurant_category": restaurant["category"],
                "restaurant_source": "amap_realtime",
                "restaurant_external_id": restaurant["external_id"],
                "name": food_name,
                "cuisine": cuisine_type,
                "price": restaurant["price"] * (0.3 + i * 0.2) if restaurant["price"] > 0 else 30.0 + i * 15,
                "rating": restaurant["rating"],
                "heat": restaurant["heat"],
                "distance": restaurant["distance"],
                "duration": restaurant["distance"] // 80,  # 步行大约80米/分钟
                "photos": restaurant.get("photos", []),
            })

    # 如果指定了菜系，过滤
    if cuisine:
        foods = [f for f in foods if cuisine.lower() in f["cuisine"].lower()]

    # 按评分从高到低排序
    foods.sort(key=lambda x: x["rating"], reverse=True)

    return {
        "items": foods[:limit],
        "total": len(foods),
        "center": result["center"],
        "radius": radius,
        "cuisines": list(set(f["cuisine"] for f in foods)),
        "source": "amap_realtime",
        "algorithm_trace": {
            "source": "amap_realtime_food_generation",
            "restaurants": len(restaurants),
            "foods_generated": len(foods),
            "coordinate": f"{lng},{lat}",
        },
    }


def _guess_cuisine_type(category: str, name: str) -> str:
    """根据类别和名称猜测菜系"""
    category_lower = category.lower()
    name_lower = name.lower()

    # 关键词匹配
    if any(k in category_lower or k in name_lower for k in ["火锅", "hot pot"]):
        return "火锅"
    elif any(k in category_lower or k in name_lower for k in ["烧烤", "烤肉", "bbq"]):
        return "烧烤"
    elif any(k in category_lower or k in name_lower for k in ["面", " noodle", "粉"]):
        return "面食"
    elif any(k in category_lower or k in name_lower for k in ["咖啡", "cafe", "奶茶"]):
        return "咖啡茶饮"
    elif any(k in category_lower or k in name_lower for k in ["西餐", "western", "汉堡", "pizza"]):
        return "西餐"
    elif any(k in category_lower or k in name_lower for k in ["日本", "寿司", "日料", "japanese"]):
        return "日料"
    elif any(k in category_lower or k in name_lower for k in ["韩国", "韩式", "korean", "炸鸡"]):
        return "韩餐"
    elif any(k in category_lower or k in name_lower for k in ["川菜", "麻辣", "辣"]):
        return "川菜"
    elif any(k in category_lower or k in name_lower for k in ["粤菜", "广东", "茶餐厅"]):
        return "粤菜"
    elif any(k in category_lower or k in name_lower for k in ["小吃", "快餐", "snack"]):
        return "小吃快餐"
    else:
        return "中餐"


def _generate_food_names(restaurant_name: str, cuisine: str) -> list[str]:
    """根据餐厅名和菜系生成菜品名"""
    # 各类型的代表性菜品
    food_templates = {
        "火锅": ["招牌锅底", "精品肥牛", "新鲜蔬菜拼盘"],
        "烧烤": ["招牌烤肉", "烤串拼盘", "特色烤蔬菜"],
        "面食": ["招牌汤面", "特色拌面", "手工饺子"],
        "咖啡茶饮": ["招牌咖啡", "季节限定茶饮", "特色甜点"],
        "西餐": ["招牌牛排", "意面套餐", "特色沙拉"],
        "日料": ["招牌寿司拼盘", "刺身套餐", "日式拉面"],
        "韩餐": ["石锅拌饭", "韩式烤肉", "部队锅"],
        "川菜": ["招牌麻辣锅", "水煮鱼", "回锅肉"],
        "粤菜": ["烧腊拼盘", "港式点心", "白切鸡"],
        "小吃快餐": ["招牌套餐", "特色小吃", "招牌汤"],
        "中餐": ["招牌菜", "特色小炒", "例汤"],
    }

    templates = food_templates.get(cuisine, ["招牌菜", "特色推荐", "厨师推荐"])
    return [f"{restaurant_name}{t}" for t in templates[:2]]
