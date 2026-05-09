"""Bootstrap helpers for sample POI data."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import POI


SAMPLE_POIS: list[dict] = [
    {
        "name": "故宫博物院",
        "city": "北京",
        "type": "景区",
        "latitude": 39.9163,
        "longitude": 116.3972,
        "floor": 1,
        "description": "北京市中心的帝制建筑群，适合历史文化体验。",
    },
    {
        "name": "天安门广场",
        "city": "北京",
        "type": "景点",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "floor": 1,
        "description": "中国首都的象征，适合城市地标与历史体验。",
    },
    {
        "name": "万里长城",
        "city": "北京",
        "type": "景区",
        "latitude": 40.4319,
        "longitude": 115.9917,
        "floor": 1,
        "description": "世界奇迹之一，适合自然风光与历史文化体验。",
    },
    {
        "name": "颐和园",
        "city": "北京",
        "type": "公园",
        "latitude": 39.9953,
        "longitude": 116.2724,
        "floor": 1,
        "description": "皇家园林，适合休闲漫步与自然风光体验。",
    },
    {
        "name": "北京动物园",
        "city": "北京",
        "type": "动物园",
        "latitude": 39.9481,
        "longitude": 116.3144,
        "floor": 1,
        "description": "国家4A级景区，适合休闲与亲子体验。",
    },
    {
        "name": "东京塔",
        "city": "东京",
        "type": "景点",
        "latitude": 35.6586,
        "longitude": 139.7454,
        "floor": 1,
        "description": "东京经典城市地标，适合城市观景。",
    },
    {
        "name": "上野公园",
        "city": "东京",
        "type": "公园",
        "latitude": 35.7156,
        "longitude": 139.7745,
        "floor": 1,
        "description": "适合休闲漫步与赏景的城市公园。",
    },
    {
        "name": "浅草寺",
        "city": "东京",
        "type": "景区",
        "latitude": 35.7148,
        "longitude": 139.7967,
        "floor": 1,
        "description": "东京人文与历史体验的重要景点。",
    },
    {
        "name": "涩谷十字路口",
        "city": "东京",
        "type": "景点",
        "latitude": 35.6595,
        "longitude": 139.7005,
        "floor": 1,
        "description": "适合城市夜景、购物与现代都市体验。",
    },
    {
        "name": "明治神宫",
        "city": "东京",
        "type": "景区",
        "latitude": 35.6764,
        "longitude": 139.6993,
        "floor": 1,
        "description": "适合休闲与历史文化体验的城市神宫。",
    },
    {
        "name": "大雁塔",
        "city": "西安",
        "type": "景区",
        "latitude": 34.2236,
        "longitude": 108.9642,
        "floor": 1,
        "description": "西安重要历史文化地标。",
    },
    {
        "name": "西安城墙",
        "city": "西安",
        "type": "景区",
        "latitude": 34.2590,
        "longitude": 108.9423,
        "floor": 1,
        "description": "适合城市历史体验与骑行观光。",
    },
    {
        "name": "大唐不夜城",
        "city": "西安",
        "type": "景点",
        "latitude": 34.2155,
        "longitude": 108.9716,
        "floor": 1,
        "description": "适合夜游、美食与城市文化体验。",
    },
    {
        "name": "陕西历史博物馆",
        "city": "西安",
        "type": "景区",
        "latitude": 34.2215,
        "longitude": 108.9531,
        "floor": 1,
        "description": "适合深度历史文化体验。",
    },
    {
        "name": "回民街",
        "city": "西安",
        "type": "景点",
        "latitude": 34.2654,
        "longitude": 108.9471,
        "floor": 1,
        "description": "适合美食、夜游与本地生活体验。",
    },
]


def sync_sample_pois(db: Session) -> int:
    """Insert missing sample POIs by name, preserving existing user data."""
    existing_names = {name for (name,) in db.query(POI.name).all()}
    inserted = 0

    for poi_data in SAMPLE_POIS:
        if poi_data["name"] in existing_names:
            continue
        db.add(POI(**poi_data))
        inserted += 1

    if inserted:
        db.commit()
    return inserted
