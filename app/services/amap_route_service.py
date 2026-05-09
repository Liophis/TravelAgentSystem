"""高德地图路线规划服务 - 获取真实的途经点"""

from typing import Optional

import requests

from app.config import get_settings


class AmapRouteService:
    """利用高德地图 API 获取驾车/步行路线途经点"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化高德地图服务
        
        Args:
            api_key: 高德地图 Web API Key（可从环境变量或参数获取）
        """
        settings = get_settings()
        self.api_key = api_key or settings.amap_web_api_key or settings.vite_amap_web_js_key
        
        self.base_url = "https://restapi.amap.com/v3/direction/driving"

    def get_route_via_amap(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        route_type: str = "0"
    ) -> dict:
        """
        调用高德地图驾车路线规划 API，获取途经点
        """
        if not self.api_key:
            print("⚠️ 高德地图 API Key 未配置")
            return {
                "success": False,
                "error": "高德地图 API Key 未配置",
                "distance": 0,
                "duration": 0,
                "steps": []
            }

        try:
            params = {
                "origin": f"{start_lon},{start_lat}",
                "destination": f"{end_lon},{end_lat}",
                "type": route_type,
                "key": self.api_key,
                "extensions": "all"
            }

            print(f"📍 调用高德地图 API: {start_lat},{start_lon} → {end_lat},{end_lon}")
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查状态：高德 API 返回字符串 "1" 表示成功
            status = data.get("status")
            if str(status) != "1":
                error_msg = data.get("info", "路线规划失败")
                print(f"❌ 高德地图 API 错误: {error_msg} (status: {status})")
                return {
                    "success": False,
                    "error": error_msg,
                    "distance": 0,
                    "duration": 0,
                    "steps": []
                }

            # 解析路线数据
            route = data.get("route", {})
            paths = route.get("paths", [])
            
            if not paths:
                print("❌ 高德地图返回无路线数据")
                return {
                    "success": False,
                    "error": "无法获取路线信息",
                    "distance": 0,
                    "duration": 0,
                    "steps": []
                }

            path = paths[0]
            distance = int(path.get("distance", 0))
            duration = int(path.get("duration", 0))
            steps = path.get("steps", [])

            print(f"✅ 路线规划成功: {distance}m, {duration}秒, {len(steps)} 步")

            # 关键优化：只提取每个 step 的关键点（起始点），而不是 polyline 中的所有坐标
            # 这样可以将 900+ 个点减少到 50-100 个关键转折点
            waypoints = []
            
            # 添加起点
            waypoints.append({
                "lng": start_lon,
                "lat": start_lat,
                "action": "开始",
                "distance": 0,
                "duration": 0
            })

            # 从每个 step 中智能提取关键点
            accumulated_distance = 0
            accumulated_duration = 0
            
            for step_idx, step in enumerate(steps):
                polyline = step.get("polyline", "")
                instruction = step.get("instruction", "")
                step_distance = int(step.get("distance", 0))
                step_duration = int(step.get("duration", 0))
                
                accumulated_distance += step_distance
                accumulated_duration += step_duration
                
                if polyline:
                    coords = polyline.split(";")
                    # 只提取每个 step 的第一个和最后一个点（关键转折点）
                    key_coords = [coords[0]] if coords else []
                    if len(coords) > 1:
                        key_coords.append(coords[-1])
                    
                    for coord in key_coords:
                        if "," in coord:
                            parts = coord.split(",")
                            if len(parts) >= 2:
                                try:
                                    # 高德 polyline 的格式是 "lng,lat"
                                    lng = float(parts[0])
                                    lat = float(parts[1])
                                    # 避免重复和微小的移动
                                    if not waypoints or (waypoints[-1]["lat"], waypoints[-1]["lng"]) != (lat, lng):
                                        waypoints.append({
                                            "lat": lat,
                                            "lng": lng,
                                            "action": instruction or f"转向点 {len(waypoints)}",
                                            "distance": step_distance,
                                            "duration": step_duration
                                        })
                                except ValueError:
                                    pass

            # 添加终点
            if not waypoints or (waypoints[-1]["lat"], waypoints[-1]["lng"]) != (end_lat, end_lon):
                waypoints.append({
                    "lng": end_lon,
                    "lat": end_lat,
                    "action": "到达",
                    "distance": 0,
                    "duration": 0
                })

            print(f"📌 优化后提取了 {len(waypoints)} 个关键转折点（原始 {len(steps)} 步）")

            return {
                "success": True,
                "distance": distance,
                "duration": duration,
                "steps": waypoints,
                "error": None
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ 高德 API 请求失败: {str(e)}")
            return {
                "success": False,
                "error": f"请求高德 API 失败: {str(e)}",
                "distance": 0,
                "duration": 0,
                "steps": []
            }
        except Exception as e:
            print(f"❌ 解析路线数据失败: {str(e)}")
            return {
                "success": False,
                "error": f"解析路线数据失败: {str(e)}",
                "distance": 0,
                "duration": 0,
                "steps": []
            }
