#!/usr/bin/env python
"""初始化脚本 - 创建示例数据"""

from app.db.database import SessionLocal, engine
from app.db.models import Base, POI, User, Facility, TravelDiary


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
                type="景区",
                latitude=39.9163,
                longitude=116.3972,
                floor=1,
                description="北京市中心的帝制建筑群",
            ),
            POI(
                name="天安门广场",
                type="景点",
                latitude=39.9042,
                longitude=116.4074,
                floor=1,
                description="中国首都的象征",
            ),
            POI(
                name="万里长城",
                type="景区",
                latitude=40.4319,
                longitude=115.9917,
                floor=1,
                description="世界奇迹之一",
            ),
            POI(
                name="颐和园",
                type="公园",
                latitude=39.9953,
                longitude=116.2724,
                floor=1,
                description="皇家园林",
            ),
            POI(
                name="北京动物园",
                type="动物园",
                latitude=39.9481,
                longitude=116.3144,
                floor=1,
                description="国家4A级景区",
            ),
        ]

        for poi in sample_pois:
            db.add(poi)

        db.commit()
        print(f"✓ 已创建 {len(sample_pois)} 个 POI")

        # 创建示例用户
        sample_users = [
            User(
                username="user_alice",
                email="alice@example.com",
                interests="历史,建筑,文化",
            ),
            User(
                username="user_bob",
                email="bob@example.com",
                interests="自然,风景,摄影",
            ),
            User(
                username="user_charlie",
                email="charlie@example.com",
                interests="美食,购物,娱乐",
            ),
        ]

        for user in sample_users:
            db.add(user)

        db.commit()
        print(f"✓ 已创建 {len(sample_users)} 个用户")

        # 创建示例设施
        sample_facilities = [
            Facility(
                name="故宫餐厅",
                type="餐厅",
                poi_id=1,
                location_desc="故宫东侧",
            ),
            Facility(
                name="游客中心",
                type="服务",
                poi_id=1,
                location_desc="故宫南门",
            ),
            Facility(
                name="停车场",
                type="停车",
                poi_id=2,
                location_desc="广场西侧",
            ),
        ]

        for facility in sample_facilities:
            db.add(facility)

        db.commit()
        print(f"✓ 已创建 {len(sample_facilities)} 个设施")

        # 创建示例日记
        sample_diaries = [
            TravelDiary(
                user_id=1,
                title="第一次去故宫",
                content="今天早起去故宫，天气很好，拍了很多照片。故宫的建筑真是太宏伟了！",
                poi_id=1,
            ),
            TravelDiary(
                user_id=1,
                title="登上长城",
                content="登上了长城的最高点，往远处眺望，真的看到了很远的地方。这次旅行收获很大。",
                poi_id=3,
            ),
            TravelDiary(
                user_id=2,
                title="颐和园漫步",
                content="在颐和园划船，欣赏了美丽的园林景观。秋天的颐和园特别迷人。",
                poi_id=4,
            ),
        ]

        for diary in sample_diaries:
            db.add(diary)

        db.commit()
        print(f"✓ 已创建 {len(sample_diaries)} 个日记")

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
