# 项目快速启动指南

## 项目结构概览

```
TravelAgentSystem/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API 路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── poi_service.py   # 景点查询服务
│   │   ├── route_service.py # 路线规划服务
│   │   ├── amap_route_service.py # 高德路线服务
│   │   └── chat_service.py  # 行程问答服务
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
│       └── chat.py          # Chat Pydantic 模型
├── requirements.txt         # Python 依赖
├── tests/
│   ├── test_api_flow.py    # 后端主闭环单元测试
│   └── test_e2e_route.sh   # 联调脚本
└── docs/README.md          # 文档入口
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

### 2.1 环境变量配置

项目现在采用集中式环境配置，参考 TripStar 的管理方式：

- 共享示例文件：`.env.example`、`frontend/.env.example`
- 本地覆盖文件：`.env.local`、`frontend/.env.local`
- 运行时优先读取 `.env.local`，再读取 `.env`

启动前请把真实密钥放到本地未提交的 `.env.local` 中，不要直接写进仓库跟踪文件。

### 3. 运行服务

```bash
# 从项目根目录运行
uvicorn app.main:app --reload --port 8000
```

### 4. 启动前端（可选）

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：`http://127.0.0.1:5173`

### 5. 访问 API

浏览器访问：`http://127.0.0.1:8000/docs`

这会打开 FastAPI 的 Swagger UI，可以在线测试所有 API 端点。

## API 端点概览

### POI（景点）相关
- `GET /api/pois` - 获取所有景点
- `GET /api/pois/search?keyword=xxx` - 按关键词搜索景点（使用 Trie 索引）
- `GET /api/pois/{poi_id}` - 获取景点详情
- `POST /api/pois` - 创建新景点

### 路线规划相关
- `GET /api/routes/{start_poi_id}/{end_poi_id}` - 规划两点间的最短路线

### 行程生成与问答
- `POST /api/trips` - 生成旅行计划
- `POST /api/chat/ask` - 基于当前旅行计划进行问答

### 设置相关
- `GET /api/settings` - 读取运行时配置
- `PUT /api/settings` - 保存运行时配置

## 核心模块说明

### 1. 数据结构 (app/core/)

- **Graph**: 邻接表实现的图，支持 add_node、add_edge、dijkstra
- **Trie**: 前缀树，用于高效的关键词搜索
- **MinHeap**: 最小堆，用于 Top-K 场景

### 2. 服务层 (app/services/)

- **POIService**: 管理景点的 CRUD、搜索、索引
- **RouteService**: 处理路线规划逻辑，优先尝试高德路线，失败后降级到本地 Dijkstra
- **Trip Generation**: 在 `/api/trips` 中完成候选筛选、Top-K 和日程组装
- **Chat Service**: 围绕当前行程生成追问回复

### 3. 数据库 (app/db/)

- **models.py**: 当前主要定义 `pois` 景点表
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

- Trie 的搜索可以继续增强为更完整的候选补全
- RouteService 可以继续收敛为更真实的图模型
- Chat Service 后续可升级为 LLM 驱动问答

## 当前建议操作

1. 先运行 `python -m unittest tests/test_api_flow.py` 验证后端主闭环。
2. 启动后端后，再运行 `bash tests/test_e2e_route.sh` 做接口联调。
3. 若继续开发，请以 `项目总览与执行说明.md` 中的 P0/P1 节奏为准。
4. P1 小红书内容增强默认可直接运行；若要注入外部样例，可设置 `XHS_SAMPLE_NOTES_PATH`，失败时会自动降级到内置内容。
5. 若要直接验证更真实外部输入，可在“运行时设置”里导入 `docs/examples/xhs_sample_notes.example.json`，或把它复制到任意绝对路径后填入 `XHS_SAMPLE_NOTES_PATH`。
6. 若你手里已经有 `TripStar` 抓下来的原始搜索/详情 JSON，可直接导入 `docs/examples/tripstar_xhs_bundle.example.json` 这种结构；若是别的采集器中间结果，可参考 `docs/examples/third_party_xhs_items.example.json`。

## 注意事项

- 数据库文件存储在项目根目录，为 `travel_agent.db`（SQLite）
- 开发时使用 `--reload` 标志，代码修改会自动重新加载
- API 文档地址：`/docs`（Swagger UI）和 `/redoc`（ReDoc）
- `test_e2e_route.sh` 依赖本地后端已启动，默认访问 `http://127.0.0.1:8000`
