<template>
  <section class="page-stack dashboard-page">
    <div class="page-heading">
      <div>
        <h1>Smart Tour Guide 数据驾驶舱</h1>
        <p>围绕旅游推荐、校内/景区导航、附近设施、游记社区、AIGC 和美食推荐组织演示入口。</p>
      </div>
      <div class="heading-actions">
        <el-button @click="refreshDashboard">刷新数据</el-button>
        <el-button type="primary" @click="$router.push('/demo')">进入答辩演示</el-button>
      </div>
    </div>

    <div class="dashboard-hero">
      <div>
        <span class="dashboard-kicker">Algorithm Service Platform</span>
        <h2>完整旅游算法服务，而不是孤立 Demo</h2>
        <p>每个核心模块都返回 algorithm_trace，前端展示算法、候选规模、返回数量和耗时信息，方便答辩时直接说明实现路径。</p>
      </div>
      <div class="dashboard-actions">
        <el-button type="primary" @click="$router.push('/profile')">AI 用户画像</el-button>
        <el-button @click="$router.push('/routes')">路线规划</el-button>
        <el-button @click="$router.push('/foods')">美食推荐</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col v-for="item in metricCards" :key="item.label" :span="6">
        <el-card shadow="never" class="metric-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.note }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="18">
      <el-col :span="15">
        <el-card shadow="never">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>核心算法能力</strong>
                <small>课程要求对应的可演示算法</small>
              </div>
              <el-tag effect="plain">Trace 可视化</el-tag>
            </div>
          </template>
          <div class="algorithm-grid">
            <article v-for="item in algorithmCards" :key="item.title" class="algorithm-card">
              <span>{{ item.stage }}</span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </article>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>当前推荐 Trace</strong>
                <small>读取推荐接口的实时算法记录</small>
              </div>
            </div>
          </template>
          <AlgorithmTracePanel :trace="recommendTrace" compact />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="8" v-for="item in visibleModules" :key="item.path">
        <el-card shadow="never" class="module-card">
          <h2>{{ item.title }}</h2>
          <p>{{ item.description }}</p>
          <el-button type="primary" plain @click="$router.push(item.path)">进入</el-button>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import AlgorithmTracePanel from "../components/AlgorithmTracePanel.vue";
import { apiGet, type RecommendationPayload } from "../services/api";
import { authState, isAdmin } from "../services/auth";

const mapStats = reactive({
  bupt: { nodes: 0, roads: 0, buildings: 0, facilities: 0 },
  summer: { nodes: 0, roads: 0, buildings: 0, facilities: 0 },
});
const destinationTotal = ref(0);
const recommendTrace = ref<Record<string, string> | null>(null);
const currentUserId = computed(() => authState.user?.id ?? 1);
const metricCards = computed(() => [
  { label: "景区/学校", value: destinationTotal.value, note: "全国真实目的地推荐池" },
  { label: "北邮校内道路", value: mapStats.bupt.roads, note: `${mapStats.bupt.buildings} 建筑 / ${mapStats.bupt.facilities} 设施` },
  { label: "颐和园道路", value: mapStats.summer.roads, note: `${mapStats.summer.buildings} 景点建筑 / ${mapStats.summer.facilities} 设施` },
  { label: "用户画像", value: currentUserId.value, note: "当前登录账号参与推荐" },
]);
const algorithmCards = [
  {
    stage: "Recommendation",
    title: "Top-K 堆推荐",
    description: "旅游推荐和美食推荐都避免完全排序，按热度、评分、兴趣和距离计算综合得分。",
  },
  {
    stage: "Navigation",
    title: "Dijkstra / 多点路线",
    description: "校内和景区内部路线基于道路图节点与边，附近设施使用真实路径距离排序。",
  },
  {
    stage: "Diary",
    title: "倒排索引 + Huffman",
    description: "游记支持标题精确查询、全文检索、浏览评分排序和压缩存储。",
  },
  {
    stage: "LLM Profile",
    title: "AI 兴趣画像",
    description: "真实可配置 LLM 调用只负责提取用户兴趣标签，推荐排序仍由确定性算法完成。",
  },
];

const modules = [
  {
    title: "答辩演示",
    description: "一页展示核心接口、算法 trace 和 ECharts 关系图。",
    path: "/demo",
  },
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
    title: "路线规划",
    description: "选择校门、楼宇、设施或命名点，绘制北邮沙河和颐和园内部路线。",
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
    description: "按菜系、热度、评分和距离推荐目的地周边餐厅与菜品。",
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

async function refreshDashboard() {
  const [destinations, bupt, summer, recommendation] = await Promise.allSettled([
    apiGet<{ total: number }>("/api/v1/destinations?limit=1"),
    apiGet<Record<string, number>>("/api/v1/map/stats?scene_key=bupt_shahe"),
    apiGet<Record<string, number>>("/api/v1/map/stats?scene_key=summer_palace"),
    apiGet<RecommendationPayload>(`/api/v1/recommendations?user_id=${currentUserId.value}&strategy=composite&limit=5`),
  ]);
  if (destinations.status === "fulfilled") destinationTotal.value = destinations.value.total;
  if (bupt.status === "fulfilled") {
    mapStats.bupt = normalizeStats(bupt.value);
  }
  if (summer.status === "fulfilled") {
    mapStats.summer = normalizeStats(summer.value);
  }
  if (recommendation.status === "fulfilled") {
    recommendTrace.value = recommendation.value.algorithm_trace;
  }
}

function normalizeStats(value: Record<string, number>) {
  return {
    nodes: value.nodes ?? 0,
    roads: value.roads ?? 0,
    buildings: value.buildings ?? 0,
    facilities: value.facilities ?? 0,
  };
}

onMounted(() => {
  void refreshDashboard();
});
</script>

<style scoped>
.dashboard-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 24px;
  border: 1px solid #d6ebe7;
  border-radius: 8px;
  background: linear-gradient(135deg, #ffffff, #f0faf8);
}

.dashboard-kicker {
  color: #0f766e;
  font-weight: 800;
}

.dashboard-hero h2 {
  margin: 8px 0;
  color: #101828;
  font-size: 28px;
  letter-spacing: 0;
}

.dashboard-hero p {
  max-width: 760px;
  margin: 0;
  color: #667085;
  line-height: 1.7;
}

.dashboard-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
  min-width: 320px;
}

.metric-card {
  min-height: 138px;
}

.metric-card span {
  color: #667085;
  font-size: 13px;
}

.metric-card strong {
  display: block;
  margin-top: 8px;
  color: #101828;
  font-size: 30px;
}

.metric-card p {
  margin: 8px 0 0;
  color: #667085;
  line-height: 1.45;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-header small {
  display: block;
  color: #667085;
  font-size: 12px;
}

.algorithm-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.algorithm-card {
  min-height: 146px;
  padding: 14px;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  background: #fcfcfd;
}

.algorithm-card span {
  color: #0f766e;
  font-size: 12px;
  font-weight: 800;
}

.algorithm-card h3 {
  margin: 8px 0;
  color: #101828;
}

.algorithm-card p {
  margin: 0;
  color: #667085;
  line-height: 1.6;
}
</style>
