"""Route Service - 处理路线规划相关的业务逻辑"""

from sqlalchemy.orm import Session

from app.core.graph import Graph
from app.db import crud
from app.services.amap_route_service import AmapRouteService


class RouteService:
    """处理路线规划、距离计算等"""

    def __init__(self, graph: Graph):
        self.graph = graph
        self.amap_service = AmapRouteService()

    def find_shortest_path(self, db: Session, start_poi_id: int, end_poi_id: int) -> dict | None:
        """查找最短路径 - 先尝试高德地图 API，失败则用本地 Dijkstra"""
        start_poi = crud.get_poi_by_id(db, start_poi_id)
        end_poi = crud.get_poi_by_id(db, end_poi_id)

        if not start_poi or not end_poi:
            return None

        # 首先尝试使用高德地图 API 获取真实路线
        amap_result = self.amap_service.get_route_via_amap(
            start_lat=start_poi.latitude,
            start_lon=start_poi.longitude,
            end_lat=end_poi.latitude,
            end_lon=end_poi.longitude
        )

        if amap_result.get("success"):
            # 高德 API 返回的距离是米，需要转换为公里
            distance_km = amap_result.get("distance", 0) / 1000.0
            duration_seconds = amap_result.get("duration", 0)
            waypoints = amap_result.get("steps", [])

            # 构建路径点数据 - 包含高德 API 返回的所有途经点
            path_nodes = []
            
            # 添加起点
            path_nodes.append({
                "id": start_poi.id,
                "name": start_poi.name,
                "latitude": start_poi.latitude,
                "longitude": start_poi.longitude,
            })

            # 添加中间途经点（不包括起点和终点）
            if len(waypoints) > 2:
                for i, waypoint in enumerate(waypoints[1:-1], 1):
                    path_nodes.append({
                        "id": f"wp_{i}",
                        "name": waypoint.get("action", f"转折点 {i}"),
                        "latitude": waypoint.get("lat"),
                        "longitude": waypoint.get("lng"),
                    })

            # 添加终点
            path_nodes.append({
                "id": end_poi.id,
                "name": end_poi.name,
                "latitude": end_poi.latitude,
                "longitude": end_poi.longitude,
            })

            # 估算驾车时间（秒转小时）
            estimated_hours = duration_seconds / 3600.0 if duration_seconds > 0 else distance_km / 40.0

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
                "distance": round(distance_km, 4),
                "estimated_time_hours": round(estimated_hours, 3),
                "source": "amap"
            }

        # 降级：使用本地 Dijkstra 算法
        return self._dijkstra_route(db, start_poi, end_poi)

    def _dijkstra_route(self, db: Session, start_poi, end_poi) -> dict:
        """使用 Dijkstra 算法规划路线（降级方案）"""
        
        def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            from math import radians, sin, cos, sqrt, asin
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            R = 6371.0
            return R * c

        # 加载图数据
        if not self.graph.nodes:
            pois = crud.get_all_pois(db, skip=0, limit=10000)
            for poi in pois:
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

        # 构建完全图边
        any_edges = any(len(edges) > 0 for edges in self.graph.adjacency_list.values())
        if not any_edges:
            nodes = list(self.graph.nodes.items())
            for nid, node in nodes:
                lat1 = node.data.get("latitude") if node.data else None
                lon1 = node.data.get("longitude") if node.data else None
                if lat1 is None or lon1 is None:
                    continue
                for mid, mnode in nodes:
                    if nid == mid:
                        continue
                    lat2 = mnode.data.get("latitude") if mnode.data else None
                    lon2 = mnode.data.get("longitude") if mnode.data else None
                    if lat2 is None or lon2 is None:
                        continue
                    dist = haversine(lat1, lon1, lat2, lon2)
                    self.graph.add_edge(nid, mid, dist)

        # 运行 Dijkstra 算法
        path_node_ids = self.graph.dijkstra(str(start_poi.id), str(end_poi.id))

        # 计算路线距离
        total_distance_km = 0.0
        path_coords = []
        if path_node_ids:
            for pid in path_node_ids:
                node = self.graph.nodes.get(pid)
                if node and node.data:
                    path_coords.append({
                        "id": int(pid),
                        "name": node.data.get("name"),
                        "latitude": node.data.get("latitude"),
                        "longitude": node.data.get("longitude"),
                    })

            for a, b in zip(path_node_ids, path_node_ids[1:]):
                found = False
                for neigh, w in self.graph.adjacency_list.get(a, []):
                    if neigh == b:
                        total_distance_km += w
                        found = True
                        break
                if not found:
                    na = self.graph.nodes.get(a)
                    nb = self.graph.nodes.get(b)
                    if na and nb and na.data and nb.data:
                        total_distance_km += haversine(
                            na.data.get("latitude"),
                            na.data.get("longitude"),
                            nb.data.get("latitude"),
                            nb.data.get("longitude"),
                        )

        avg_speed_kmh = 40.0
        estimated_hours = total_distance_km / avg_speed_kmh if avg_speed_kmh > 0 else 0

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
            "path_nodes": path_coords,
            "distance": round(total_distance_km, 4),
            "estimated_time_hours": round(estimated_hours, 3),
            "source": "dijkstra"
        }

    def add_edge(self, from_poi_id: int, to_poi_id: int, distance: float) -> None:
        """在图中添加边（连接两个景点）"""
        self.graph.add_edge(str(from_poi_id), str(to_poi_id), distance)

    def get_nearby_pois(self, db: Session, poi_id: int, radius_km: float = 1.0) -> list[dict]:
        """获取距离某个 POI 指定范围内的景点"""
        return []
