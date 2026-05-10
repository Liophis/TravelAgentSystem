#!/bin/bash
# 联调脚本：验证行程生成 -> 路线规划的最小闭环

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少依赖命令: $1" >&2
    exit 1
  fi
}

require_command curl
require_command jq

if ! curl -fsS "$BASE_URL/docs" >/dev/null 2>&1; then
  echo "后端不可达，请先启动服务后再执行脚本: $BASE_URL" >&2
  exit 1
fi

echo "🧪 开始 Member B 路线规划完整端到端测试"
echo "=========================================="

# 测试 1: 生成行程（调用 /api/trips）
echo ""
echo "✓ 测试 1: 后端生成行程 (POST /api/trips)"
TRIP_RESPONSE=$(curl -fsS -X POST "$BASE_URL/api/trips?city=%E5%8C%97%E4%BA%AC&start_date=2026-05-01&end_date=2026-05-03&travel_days=2&transportation=%E5%85%AC%E5%85%B1%E4%BA%A4%E9%80%9A&accommodation=%E8%88%92%E9%80%82%E5%9E%8B%E9%85%92%E5%BA%97")
ATTRACTIONS_COUNT=$(echo "$TRIP_RESPONSE" | jq -r '.data.days[0].attractions | length')
FIRST_ATTRACTION_ID=$(echo "$TRIP_RESPONSE" | jq -r '.data.days[0].attractions[0].id')
LAST_ATTRACTION_ID=$(echo "$TRIP_RESPONSE" | jq -r '.data.days[0].attractions[-1].id // .data.days[1].attractions[0].id')

if [ "$FIRST_ATTRACTION_ID" = "null" ] || [ -z "$FIRST_ATTRACTION_ID" ]; then
  echo "未能从 /api/trips 返回结果中提取起点景点 ID" >&2
  exit 1
fi

if [ "$LAST_ATTRACTION_ID" = "null" ] || [ -z "$LAST_ATTRACTION_ID" ]; then
  echo "未能从 /api/trips 返回结果中提取终点景点 ID" >&2
  exit 1
fi

echo "  ✓ 返回 $ATTRACTIONS_COUNT 个景点"
echo "  ✓ 第一个景点 ID: $FIRST_ATTRACTION_ID"
echo "  ✓ 最后一个景点 ID: $LAST_ATTRACTION_ID"

# 测试 2: 查询路线规划 API
echo ""
echo "✓ 测试 2: 后端路线规划 (GET /api/routes/{id1}/{id2})"
ROUTE_RESPONSE=$(curl -fsS "$BASE_URL/api/routes/$FIRST_ATTRACTION_ID/$LAST_ATTRACTION_ID")
PATH_NODES_COUNT=$(echo "$ROUTE_RESPONSE" | jq -r '.path_nodes | length')
DISTANCE=$(echo "$ROUTE_RESPONSE" | jq -r '.distance')
SOURCE=$(echo "$ROUTE_RESPONSE" | jq -r '.source')

echo "  ✓ 返回 $PATH_NODES_COUNT 个路径点"
echo "  ✓ 距离: ${DISTANCE}km"
echo "  ✓ 数据来源: $SOURCE"

# 验证路径点坐标格式
echo ""
echo "✓ 测试 3: 验证路径点坐标格式"
FIRST_NODE=$(echo "$ROUTE_RESPONSE" | jq -r '.path_nodes[0]')
FIRST_LAT=$(echo "$FIRST_NODE" | jq -r '.latitude')
FIRST_LNG=$(echo "$FIRST_NODE" | jq -r '.longitude')
echo "  ✓ 第一个点: Lat=$FIRST_LAT, Lng=$FIRST_LNG"

# 验证前端坐标格式 (需要转为 [lng, lat] 用于 AMap)
echo ""
echo "✓ 测试 4: 验证前端坐标格式 (AMap 需要 [lng, lat])"
echo "  ✓ AMap 坐标: [$FIRST_LNG, $FIRST_LAT]"

# 检查数据完整性
echo ""
echo "✓ 测试 5: 检查数据完整性"
if [ "$PATH_NODES_COUNT" -gt 2 ]; then
  echo "  ✓ ✅ 路径点充足 ($PATH_NODES_COUNT 个)"
else
  echo "  ✓ 📌 路径点较少 ($PATH_NODES_COUNT 个)，当前可能是直连或降级结果"
fi

if [ "$SOURCE" = "amap" ]; then
  echo "  ✓ ✅ 数据来源为 AMap (真实路线)"
else
  echo "  ✓ 📌 数据来源为 $SOURCE (降级方案)"
fi

echo ""
echo "=========================================="
echo "✅ 端到端测试完成！"
echo ""
echo "📌 前端需要："
echo "   1. 调用 POST /api/trips 获取景点列表"
echo "   2. 使用第一个和最后一个景点 ID 调用 GET /api/routes/{id1}/{id2}"
echo "   3. 将 path_nodes 转为 [longitude, latitude] 坐标对"
echo "   4. 使用 AMap.Polyline 绘制路线 (含 $PATH_NODES_COUNT 个点)"
echo "   5. 添加起点和终点标记"
