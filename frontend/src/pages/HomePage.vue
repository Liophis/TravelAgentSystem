<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>Smart Tour Guide</h1>
        <p>请选择要演示的旅游算法服务。推荐、导航、设施、游记社区、AIGC 创作和美食模块保持独立入口。</p>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="8" v-for="item in visibleModules" :key="item.path">
        <el-card shadow="never" class="module-card">
          <h2>{{ item.title }}</h2>
          <p>{{ item.description }}</p>
          <el-button type="primary" @click="$router.push(item.path)">进入</el-button>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { isAdmin } from "../services/auth";

const modules = [
  {
    title: "个人偏好",
    description: "维护当前账号的兴趣画像、收藏、评分和浏览行为。",
    path: "/profile",
  },
  {
    title: "地图与目的地",
    description: "在地图上浏览景区/学校 POI，也可切换校区和景区内部图层。",
    path: "/map",
  },
  {
    title: "校内导航",
    description: "选择校门、楼宇、设施或命名校内点，使用参考校园拓扑绘制校内路线。",
    path: "/routes",
  },
  {
    title: "附近设施",
    description: "按类别查询设施，并使用道路图距离进行 Top-K 排序。",
    path: "/facilities",
  },
  {
    title: "游记社区",
    description: "查询、浏览、评分和评论所有用户的目的地游记。",
    path: "/diaries",
  },
  {
    title: "发布与 AIGC",
    description: "发布景区或学校游记，并用 Agent 生成分镜和模拟视频。",
    path: "/diaries/create",
  },
  {
    title: "美食推荐",
    description: "按菜系、热度、评分和距离推荐校区餐厅与菜品。",
    path: "/foods",
  },
  {
    title: "管理后台",
    description: "查看地图、用户、目的地、游记和美食数据规模。",
    path: "/admin",
    adminOnly: true,
  },
];

const visibleModules = computed(() => modules.filter((item) => !item.adminOnly || isAdmin()));
</script>

<style scoped>
.module-card {
  min-height: 180px;
}

.module-card h2 {
  margin: 0 0 10px;
  color: #101828;
  font-size: 18px;
}

.module-card p {
  min-height: 52px;
  margin: 0 0 18px;
  color: #667085;
  line-height: 1.55;
}
</style>
