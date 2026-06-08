<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>Smart Tour Guide</h1>
        <p>北京邮电大学沙河校区导览、路线、设施、搜索与推荐演示。</p>
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

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>推荐目的地</span>
          <el-segmented v-model="strategy" :options="strategyOptions" @change="() => loadRecommendations()" />
        </div>
      </template>
      <el-row :gutter="12">
        <el-col v-for="item in recommendations" :key="item.id" :span="8">
          <div class="recommendation-item">
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.reason }}</p>
            </div>
            <div class="recommendation-score">{{ item.score?.toFixed(2) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { apiGet, type DestinationItem, type RecommendationPayload } from "../services/api";

const strategy = ref("composite");
const recommendations = ref<DestinationItem[]>([]);
const strategyOptions = [
  { label: "综合", value: "composite" },
  { label: "热门", value: "hot" },
  { label: "高分", value: "rating" },
  { label: "兴趣", value: "interest" },
];
const modules = [
  {
    title: "个人偏好",
    description: "选择兴趣标签，查看随用户画像变化的推荐结果。",
    path: "/profile",
  },
  {
    title: "目的地",
    description: "浏览 200 个演示目的地，支持分类筛选、关键词搜索和详情查看。",
    path: "/destinations",
  },
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
    description: "按类别查询设施，并使用道路图距离进行 Top-K 排序。",
    path: "/facilities",
  },
  {
    title: "游记社区",
    description: "发布、搜索、评分和评论游记，并展示文本压缩统计。",
    path: "/diaries",
  },
  {
    title: "美食推荐",
    description: "按菜系、热度、评分和距离推荐校区餐厅与菜品。",
    path: "/foods",
  },
  {
    title: "AIGC 辅助",
    description: "生成游记草稿、标题和短视频分镜提示词。",
    path: "/aigc",
  },
  {
    title: "管理后台",
    description: "查看地图、用户、目的地、游记和美食数据规模。",
    path: "/admin",
  },
];

async function loadRecommendations() {
  const payload = await apiGet<RecommendationPayload>(`/api/v1/recommendations?user_id=1&strategy=${strategy.value}&limit=10`);
  recommendations.value = payload.items;
}

onMounted(() => {
  void loadRecommendations();
});
</script>

<style scoped>
.card-header,
.recommendation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.recommendation-item {
  min-height: 118px;
  margin-bottom: 12px;
  padding: 14px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
}

.recommendation-item p {
  margin: 6px 0 0;
  color: #667085;
  line-height: 1.5;
}

.recommendation-score {
  font-size: 20px;
  font-weight: 700;
  color: #176b87;
}
</style>
