<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>项目第一阶段基座</h1>
        <p>后端 OSM 拓扑接口与前端高德展示层已按边界拆分，当前使用 mock 数据验证页面闭环。</p>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :span="8" v-for="item in modules" :key="item.path">
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
const modules = [
  {
    title: "地图导览",
    description: "展示道路、建筑区域和设施点，并支持设施类别过滤。",
    path: "/map",
  },
  {
    title: "路线规划",
    description: "调用路线规划接口，绘制路径并展示距离、时间和步骤。",
    path: "/routes",
  },
  {
    title: "附近设施",
    description: "查询当前位置附近设施，保留真实道路距离排序接口。",
    path: "/facilities",
  },
];
</script>
