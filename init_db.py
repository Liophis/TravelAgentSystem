#!/usr/bin/env python
"""初始化脚本 - 创建示例数据"""

from app.db.database import SessionLocal, engine
from app.db.bootstrap import SAMPLE_POIS
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
        sample_pois = [POI(**poi_data) for poi_data in SAMPLE_POIS]

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
