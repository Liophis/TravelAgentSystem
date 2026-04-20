

```
|-- /app
| |-- /api
| | |-- init.py
| | |-- routes.py # 存放所有 API 路由接口
| |
| |-- /core
| | |-- init.py
| | |-- graph.py # 【手写】图数据结构与寻路算法
| | |-- heap.py # 【手写】用于 Top-K 推荐的堆
| | |-- trie.py # 【手写】用于名称模糊搜索的字典树
| |
| |-- /models
| | |-- init.py
| | |-- poi.py # POI（兴趣点）的 Pydantic 数据模型
| | |-- user.py # 用户的 Pydantic 数据模型
| |
| |-- /db
| | |-- init.py
| | |-- database.py # 数据库连接（SQLAlchemy）与会话管理
| | |-- crud.py # 封装所有数据库的增删改查（CRUD）操作
| | |-- models.py # 定义所有数据库表的 SQLAlchemy 模型
| |
| |-- init.py
| |-- main.py # FastAPI 应用的入口文件
|
|-- requirements.txt # 项目依赖
|-- .gitignore # Git 忽略文件配置
```