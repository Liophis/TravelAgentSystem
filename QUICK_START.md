# 项目最小框架快速启动指南

## 项目结构概览

```
TravelAgentSystem/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API 路由（已完善的多个端点）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── poi_service.py   # 景点查询服务
│   │   ├── route_service.py # 路线规划服务
│   │   ├── recommendation_service.py  # 推荐服务
│   │   └── diary_service.py # 日记管理服务
│   ├── core/
│   │   ├── __init__.py
│   │   ├── graph.py         # 图数据结构（用于路径规划）
│   │   ├── trie.py          # Trie 数据结构（用于前缀搜索）
│   │   └── heap.py          # 堆数据结构（用于 Top-K）
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py      # 数据库连接配置
│   │   ├── models.py        # SQLAlchemy ORM 模型
│   │   └── crud.py          # 数据库操作
│   └── models/
│       ├── __init__.py
│       ├── poi.py           # POI Pydantic 模型
│       ├── user.py          # 用户 Pydantic 模型
│       ├── diary.py         # 日记 Pydantic 模型
│       └── facility.py      # 设施 Pydantic 模型
├── requirements.txt         # Python 依赖
└── README.md               # 本文件
```

## 快速启动

### 1. 创建虚拟环境

```bash
# 使用 Python venv
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活虚拟环境（Linux/Mac）
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行服务

```bash
# 从项目根目录运行
uvicorn app.main:app --reload --port 8001
```

### 4. 访问 API

浏览器访问：`http://127.0.0.1:8001/docs`

这会打开 FastAPI 的 Swagger UI，可以在线测试所有 API 端点。

## API 端点概览

### POI（景点）相关
- `GET /api/pois` - 获取所有景点
- `GET /api/pois/search?keyword=xxx` - 按关键词搜索景点（使用 Trie 索引）
- `GET /api/pois/{poi_id}` - 获取景点详情
- `POST /api/pois` - 创建新景点

### 路线规划相关
- `GET /api/routes/{start_poi_id}/{end_poi_id}` - 规划两点间的最短路线

### 用户相关
- `POST /api/users` - 创建新用户
- `GET /api/users/{user_id}` - 获取用户信息

### 日记相关
- `POST /api/diaries?user_id=1&title=xxx&content=xxx` - 创建日记
- `GET /api/diaries/{user_id}` - 获取用户所有日记
- `GET /api/diaries/{user_id}/search?keyword=xxx` - 搜索日记

### 推荐相关
- `GET /api/recommendations/top-k?k=10` - 获取评分最高的景点
- `GET /api/recommendations/users/{user_id}?k=10` - 为用户推荐景点

## 核心模块说明

### 1. 数据结构 (app/core/)

- **Graph**: 邻接表实现的图，支持 add_node、add_edge、dijkstra
- **Trie**: 前缀树，用于高效的关键词搜索
- **MinHeap**: 最小堆，用于 Top-K 场景

### 2. 服务层 (app/services/)

- **POIService**: 管理景点的 CRUD、搜索、索引
- **RouteService**: 处理路线规划逻辑
- **RecommendationService**: 使用堆实现 Top-K 推荐
- **DiaryService**: 管理旅游日记

### 3. 数据库 (app/db/)

- **models.py**: 定义了 4 张表
  - `pois` - 景点表
  - `users` - 用户表
  - `facilities` - 设施表
  - `travel_diaries` - 日记表
- **crud.py**: 提供了对应的增删改查操作
- **database.py**: SQLite 数据库连接配置

### 4. API 层 (app/api/)

- 使用 FastAPI Router，支持完整的 CRUD 操作
- 集成了 Pydantic 模型进行请求/响应验证

## 开发指南

### 添加新的 API 端点

1. 在 `app/api/routes.py` 中添加新的路由函数
2. 使用 `@router.get()` 或 `@router.post()` 装饰器
3. 定义请求/响应模型

示例：

```python
@router.get("/api/example/{id}", response_model=ExampleSchema)
def get_example(id: int, db: Session = Depends(get_db)):
    # 业务逻辑
    pass
```

### 扩展数据库模型

1. 在 `app/db/models.py` 中定义新的 ORM 模型
2. 在 `app/db/crud.py` 中实现对应的 CRUD 操作
3. 在 `app/models/` 中创建对应的 Pydantic 模型

### 优化算法实现

- Graph 的 dijkstra 方法需要完整的 Dijkstra 算法实现
- Trie 的搜索可以支持更复杂的模糊匹配
- 推荐服务可以集成更复杂的评分逻辑

## 下一步任务

1. **完成 Dijkstra 算法**: Graph 类的 dijkstra 方法需要完整实现
2. **支持距离计算**: 基于坐标计算两点之间的真实距离
3. **倒排索引**: 实现日记的全文检索功能
4. **Huffman 编码**: 实现日记内容的无损压缩
5. **前端集成**: 开发 Vue 3 前端，集成地图展示等

## 注意事项

- 数据库文件存储在项目根目录，为 `travel_agent.db`（SQLite）
- 开发时使用 `--reload` 标志，代码修改会自动重新加载
- API 文档地址：`/docs`（Swagger UI）和 `/redoc`（ReDoc）
