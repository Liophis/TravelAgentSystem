"""POI Service - 处理景点相关的业务逻辑"""

from sqlalchemy.orm import Session

from app.core.graph import Graph
from app.core.trie import Trie
from app.db import crud
from app.models.poi import POISchema


class POIService:
    """处理景点查询、搜索和初始化"""

    def __init__(self):
        self.trie = Trie()  # 用于前缀搜索
        self.graph = Graph()  # 路径规划用的图

    def initialize_poi_index(self, db: Session) -> None:
        """从数据库加载所有 POI，构建 Trie 索引和图"""
        pois = crud.get_all_pois(db, skip=0, limit=10000)

        for poi in pois:
            # 构建 Trie 索引
            self.trie.insert(poi.name)

            # 构建图节点
            self.graph.add_node(
                str(poi.id),
                {
                    "name": poi.name,
                    "type": poi.type,
                    "latitude": poi.latitude,
                    "longitude": poi.longitude,
                    "floor": poi.floor,
                },
            )

    def search_poi(self, db: Session, keyword: str, limit: int = 10) -> list[POISchema]:
        """使用 Trie 索引进行前缀搜索"""
        # 使用 Trie 进行前缀匹配
        matches = self.trie.starts_with(keyword, limit=limit)

        result = []
        for match in matches:
            poi = crud.get_poi_by_name(db, match)
            if poi:
                result.append(
                    POISchema(
                        id=poi.id,
                        name=poi.name,
                        type=poi.type,
                        latitude=poi.latitude,
                        longitude=poi.longitude,
                        floor=poi.floor,
                        description=poi.description,
                    )
                )
        return result

    def get_poi_details(self, db: Session, poi_id: int) -> POISchema | None:
        """获取景点详情"""
        poi = crud.get_poi_by_id(db, poi_id)
        if not poi:
            return None

        return POISchema(
            id=poi.id,
            name=poi.name,
            type=poi.type,
            latitude=poi.latitude,
            longitude=poi.longitude,
            floor=poi.floor,
            description=poi.description,
        )

    def create_poi(self, db: Session, poi: POISchema) -> POISchema:
        """创建新的 POI"""
        db_poi = crud.create_poi(db, poi)

        # 更新索引
        self.trie.insert(db_poi.name)
        self.graph.add_node(
            str(db_poi.id),
            {
                "name": db_poi.name,
                "type": db_poi.type,
                "latitude": db_poi.latitude,
                "longitude": db_poi.longitude,
                "floor": db_poi.floor,
            },
        )

        return POISchema(
            id=db_poi.id,
            name=db_poi.name,
            type=db_poi.type,
            latitude=db_poi.latitude,
            longitude=db_poi.longitude,
            floor=db_poi.floor,
            description=db_poi.description,
        )
