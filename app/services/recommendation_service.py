"""Recommendation Service - 处理个性化推荐相关的业务逻辑"""

from sqlalchemy.orm import Session

from app.core.heap import MinHeap
from app.db import crud


class RecommendationService:
    """处理景点推荐、热度评分等"""

    def __init__(self):
        pass

    def get_top_k_pois(self, db: Session, k: int = 10) -> list[dict]:
        """获取评分最高的 Top-K 景点"""
        all_pois = crud.get_all_pois(db, skip=0, limit=10000)

        # 构建评分列表（目前使用固定评分，后续可改为多维度评分）
        items = [(float(poi.id), poi) for poi in all_pois]

        # 使用手写 Min-Heap 获取 Top-K
        heap = MinHeap()
        for score, poi in items:
            if len(heap) < k:
                heap.push((score, poi))
            else:
                heap.pushpop((score, poi))

        result = []
        for score, poi in heap.to_sorted_desc():
            result.append(
                {
                    "id": poi.id,
                    "name": poi.name,
                    "type": poi.type,
                    "latitude": poi.latitude,
                    "longitude": poi.longitude,
                    "score": score,
                }
            )
        return result

    def recommend_by_interest(self, db: Session, user_id: int, k: int = 10) -> list[dict]:
        """基于用户兴趣标签的推荐"""
        user = crud.get_user_by_id(db, user_id)
        if not user:
            return []

        # 后续实现基于用户兴趣与 POI 标签的相似度匹配
        return self.get_top_k_pois(db, k)
