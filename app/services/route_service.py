"""Route Service - 处理路线规划相关的业务逻辑"""

from sqlalchemy.orm import Session

from app.core.graph import Graph
from app.db import crud


class RouteService:
    """处理路线规划、距离计算等"""

    def __init__(self, graph: Graph):
        self.graph = graph

    def find_shortest_path(self, db: Session, start_poi_id: int, end_poi_id: int) -> dict | None:
        """查找最短路径"""
        start_poi = crud.get_poi_by_id(db, start_poi_id)
        end_poi = crud.get_poi_by_id(db, end_poi_id)

        if not start_poi or not end_poi:
            return None

        # 使用图的 Dijkstra 算法（目前是占位实现）
        path_nodes = self.graph.dijkstra(str(start_poi_id), str(end_poi_id))

        return {
            "start_poi": {
                "id": start_poi.id,
                "name": start_poi.name,
                "latitude": start_poi.latitude,
                "longitude": start_poi.longitude,
            },
            "end_poi": {
                "id": end_poi.id,
                "name": end_poi.name,
                "latitude": end_poi.latitude,
                "longitude": end_poi.longitude,
            },
            "path_nodes": path_nodes,
            "distance": 0.0,  # 待计算
            "estimated_time": 0,  # 待计算
        }

    def add_edge(self, from_poi_id: int, to_poi_id: int, distance: float) -> None:
        """在图中添加边（连接两个景点）"""
        self.graph.add_edge(str(from_poi_id), str(to_poi_id), distance)

    def get_nearby_pois(self, db: Session, poi_id: int, radius_km: float = 1.0) -> list[dict]:
        """获取距离某个 POI 指定范围内的景点（后续可使用地理坐标计算）"""
        # 这是占位实现，后续需要基于坐标计算距离
        return []
