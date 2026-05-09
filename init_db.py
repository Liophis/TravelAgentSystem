#!/usr/bin/env python
"""初始化脚本 - 创建示例数据"""

from app.db.database import SessionLocal, engine
from app.db.models import Base, POI


def init_db():
    """创建所有表并填充示例数据"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表已创建")

    # 获取数据库会话
    db = SessionLocal()

    try:
        # 检查是否已有数据
        existing_pois = db.query(POI).count()
        if existing_pois > 0:
            print("✓ 数据库已有数据，跳过初始化")
            return

        # 创建示例 POI
        sample_pois = [
            POI(
                name="故宫博物院",
                city="北京",
                type="景区",
                latitude=39.9163,
                longitude=116.3972,
                floor=1,
                description="北京市中心的帝制建筑群",
            ),
            POI(
                name="天安门广场",
                city="北京",
                type="景点",
                latitude=39.9042,
                longitude=116.4074,
                floor=1,
                description="中国首都的象征",
            ),
            POI(
                name="万里长城",
                city="北京",
                type="景区",
                latitude=40.4319,
                longitude=115.9917,
                floor=1,
                description="世界奇迹之一",
            ),
            POI(
                name="颐和园",
                city="北京",
                type="公园",
                latitude=39.9953,
                longitude=116.2724,
                floor=1,
                description="皇家园林",
            ),
            POI(
                name="北京动物园",
                city="北京",
                type="动物园",
                latitude=39.9481,
                longitude=116.3144,
                floor=1,
                description="国家4A级景区",
            ),
            POI(
                name="东京塔",
                city="东京",
                type="景点",
                latitude=35.6586,
                longitude=139.7454,
                floor=1,
                description="东京经典城市地标，适合城市观景。",
            ),
            POI(
                name="上野公园",
                city="东京",
                type="公园",
                latitude=35.7156,
                longitude=139.7745,
                floor=1,
                description="适合休闲漫步与赏景的城市公园。",
            ),
            POI(
                name="浅草寺",
                city="东京",
                type="景区",
                latitude=35.7148,
                longitude=139.7967,
                floor=1,
                description="东京人文与历史体验的重要景点。",
            ),
            POI(
                name="大雁塔",
                city="西安",
                type="景区",
                latitude=34.2236,
                longitude=108.9642,
                floor=1,
                description="西安重要历史文化地标。",
            ),
            POI(
                name="西安城墙",
                city="西安",
                type="景区",
                latitude=34.2590,
                longitude=108.9423,
                floor=1,
                description="适合城市历史体验与骑行观光。",
            ),
            POI(
                name="大唐不夜城",
                city="西安",
                type="景点",
                latitude=34.2155,
                longitude=108.9716,
                floor=1,
                description="适合夜游、美食与城市文化体验。",
            ),
        ]

        for poi in sample_pois:
            db.add(poi)

        db.commit()
        print(f"✓ 已创建 {len(sample_pois)} 个 POI")

        print("\n✓ 数据库初始化完成！")
        print("\n可以访问 http://127.0.0.1:8001/docs 进行 API 测试")

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
