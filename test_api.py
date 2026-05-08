#!/usr/bin/env python
"""简单的 API 测试脚本"""

import requests

BASE_URL = "http://127.0.0.1:8001/api"


def test_api():
    """测试主要的 API 端点"""

    print("=" * 50)
    print("旅游系统 API 测试")
    print("=" * 50)

    # 1. 获取所有 POI
    print("\n[1] 获取所有 POI")
    response = requests.get(f"{BASE_URL}/pois")
    print(f"状态码: {response.status_code}")
    print(f"景点数量: {response.json().get('total', 0)}")

    # 2. 创建新的 POI
    print("\n[2] 创建新的 POI")
    new_poi = {
        "name": "测试景点",
        "type": "测试",
        "latitude": 39.0,
        "longitude": 116.0,
        "floor": 1,
        "description": "这是一个测试景点",
    }
    response = requests.post(f"{BASE_URL}/pois", json=new_poi)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        poi_id = response.json().get("id")
        print(f"创建成功，POI ID: {poi_id}")

    # 3. 搜索 POI
    print("\n[3] 搜索 POI (关键词: '故宫')")
    response = requests.get(f"{BASE_URL}/pois/search", params={"keyword": "故宫"})
    print(f"状态码: {response.status_code}")
    results = response.json()
    print(f"搜索结果数量: {len(results)}")
    for poi in results[:2]:
        print(f"  - {poi['name']} ({poi['type']})")

    # 4. 创建用户
    print("\n[4] 创建用户")
    new_user = {
        "username": "test_user_123",
        "email": "test@example.com",
        "interests": "旅游,美食,风景",
    }
    response = requests.post(f"{BASE_URL}/users", json=new_user)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        user_id = response.json().get("id")
        print(f"用户创建成功，User ID: {user_id}")

    # 5. 创建日记
    print("\n[5] 创建日记")
    response = requests.post(
        f"{BASE_URL}/diaries",
        params={
            "user_id": 1,
            "title": "测试日记",
            "content": "这是一个测试日记的内容",
            "poi_id": 1,
        },
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        diary_id = response.json().get("id")
        print(f"日记创建成功，Diary ID: {diary_id}")

    # 6. 获取用户日记
    print("\n[6] 获取用户日记")
    response = requests.get(f"{BASE_URL}/diaries/1")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"日记数量: {data.get('total', 0)}")

    # 7. 搜索日记
    print("\n[7] 搜索日记")
    response = requests.get(f"{BASE_URL}/diaries/1/search", params={"keyword": "宫"})
    print(f"状态码: {response.status_code}")
    results = response.json()
    print(f"搜索结果数量: {len(results)}")

    # 8. 获取 Top-K 推荐
    print("\n[8] 获取 Top-K 推荐")
    response = requests.get(f"{BASE_URL}/recommendations/top-k", params={"k": 5})
    print(f"状态码: {response.status_code}")
    results = response.json()
    print(f"推荐景点数量: {len(results)}")

    # 9. 获取用户推荐
    print("\n[9] 获取用户推荐")
    response = requests.get(f"{BASE_URL}/recommendations/users/1", params={"k": 5})
    print(f"状态码: {response.status_code}")
    results = response.json()
    print(f"推荐景点数量: {len(results)}")

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        print("\n请确保服务已启动: uvicorn app.main:app --reload --port 8001")
