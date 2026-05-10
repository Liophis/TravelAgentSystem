

# TravelAgentSystem

这是一个前后端分离的个性化旅游系统，当前开发说明、实现状态和后续任务已经合并到主交接文档中。

## 主要文档

- [项目总览与执行说明.md](../项目总览与执行说明.md)：当前最完整的统一说明，后续 agent 优先读取。
- [项目计划.md](../项目计划.md)：原项目计划，现为历史索引。
- [项目计划书.md](../项目计划书.md)：原项目计划书，现为历史索引。
- [三人协作流程.md](../三人协作流程.md)：协作规范索引。
- [QUICK_START.md](./QUICK_START.md)：快速开始指南。
- [ROUTE_PLANNING_DIAGNOSIS.md](./ROUTE_PLANNING_DIAGNOSIS.md)：路由规划诊断和技术细节。

## 目录概览

```text
TravelAgentSystem/
├── app/                        # 后端核心代码
│   ├── api/                    # 接口层
│   │   └── routes.py           # FastAPI 路由
│   ├── services/               # 业务逻辑层
│   │   ├── amap_route_service.py    # 高德地图 API 集成
│   │   ├── poi_service.py      # POI 服务
│   │   └── route_service.py    # 路由规划服务
│   ├── core/                   # 核心算法层（手写）
│   │   ├── graph.py            # 图数据结构 & Dijkstra
│   │   ├── heap.py             # 堆数据结构
│   │   └── trie.py             # Trie 索引
│   ├── db/                     # 数据访问层
│   │   ├── crud.py             # 数据库操作
│   │   ├── database.py         # SQLAlchemy 配置
│   │   └── models.py           # ORM 模型
│   ├── models/                 # Pydantic 请求/响应模型
│   ├── config.py               # 应用配置管理
│   └── main.py                 # 后端入口
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── Landing.vue     # 首页
│   │   │   └── Result.vue      # 结果页
│   │   ├── components/         # 通用组件
│   │   ├── services/           # API 客户端和全局状态
│   │   ├── i18n/               # 国际化配置
│   │   ├── styles/             # 全局样式
│   │   ├── types/              # TypeScript 类型定义
│   │   ├── App.vue             # 全局壳层
│   │   └── main.ts             # 前端入口
│   ├── package.json            # 前端依赖
│   └── tsconfig.json           # TypeScript 配置
├── tests/                      # 测试文件
│   └── test_e2e_route.sh       # 端到端路由规划测试
├── docs/                       # 文档
│   ├── README.md               # 本文档
│   ├── QUICK_START.md          # 快速开始指南
│   └── ROUTE_PLANNING_DIAGNOSIS.md   # 技术诊断文档
├── init_db.py                  # 数据库初始化脚本
├── requirements.txt            # Python 依赖列表
├── docker-compose.yaml         # Docker 组合配置
├── Dockerfile                  # Docker 镜像定义
├── start.sh                    # 启动脚本（当前使用 uvicorn 启动 app.main:app）
├── .env                        # 环境变量模板（已脱敏）
├── .env.example                # 环境变量示例
├── .gitignore                  # Git 忽略规则
└── 项目总览与执行说明.md        # 统一交接文档（中文）
```

## 技术栈

**后端：**
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy ORM
- Pydantic v2（数据验证）
- 高德地图 API（路由规划）

**前端：**
- Vue 3 + TypeScript
- Vite（构建工具）
- Ant Design Vue（UI 组件）
- vue-i18n（国际化）
- Axios（HTTP 客户端）
- 高德地图 JS API（地图展示）

## 快速开始

详见 [QUICK_START.md](./QUICK_START.md)

## 当前第一阶段核心功能

1. **行程生成**：根据城市、日期和基础偏好生成可展示的旅行计划
2. **POI 查询**：通过 Trie 索引快速搜索旅游景点
3. **路由规划**：基于 Dijkstra 算法的最短路径规划，支持高德地图 API 补充
4. **地图展示**：AMap 交互式地图展示路由和景点
5. **行程问答**：围绕当前计划进行最小 AI Chat 问答
6. **国际化**：支持中文、英文、日文

当前 P0 主闭环已经收敛为：
`首页表单 -> /api/trips -> Result.vue -> /api/routes -> /api/chat/ask`

## 当前第一阶段公开接口

1. `GET /api/settings`
2. `PUT /api/settings`
3. `GET /api/pois`
4. `GET /api/pois/search`
5. `GET /api/pois/{poi_id}`
6. `POST /api/pois`
7. `GET /api/routes/{start_poi_id}/{end_poi_id}`
8. `POST /api/trips`
9. `POST /api/chat/ask`

## 开发规范

见 [三人协作流程.md](../三人协作流程.md) 和 [项目总览与执行说明.md](../项目总览与执行说明.md) 第 6-7 章

## 联调与验证

- 后端主闭环测试：`python -m unittest tests/test_api_flow.py`
- 路线联调脚本：`bash tests/test_e2e_route.sh`
- 前端联调前，请先确认后端服务已启动在 `http://127.0.0.1:8000`，或通过 `BASE_URL` 覆盖脚本默认地址
