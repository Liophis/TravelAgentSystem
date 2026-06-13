<template>
  <section class="page-stack demo-page">
    <div class="page-heading">
      <div>
        <h1>答辩演示页</h1>
        <p>一页串联目的地推荐、校内设施、游记、美食、用户画像和地图数据，集中展示算法 trace 与数据关系。</p>
      </div>
      <div class="heading-actions">
        <el-button :loading="profileLoading" @click="extractProfile">刷新 AI 画像</el-button>
        <el-button type="primary" :loading="loading" @click="loadDemo">重新运行演示</el-button>
      </div>
    </div>

    <div class="demo-hero">
      <div>
        <span class="hero-kicker">Stage 43</span>
        <h2>Demo Experience + LLM User Profile</h2>
        <p>课程核心算法仍由 Dijkstra、Top-K 堆、倒排索引、Huffman 和图距离排序承担；LLM 只在用户画像解释层增强兴趣标签。</p>
      </div>
      <div class="hero-metrics">
        <div><span>目的地</span><strong>{{ dashboard.destinations }}</strong></div>
        <div><span>北邮道路</span><strong>{{ dashboard.buptRoads }}</strong></div>
        <div><span>颐和园道路</span><strong>{{ dashboard.summerRoads }}</strong></div>
        <div><span>演示接口</span><strong>{{ demoCards.length }}</strong></div>
      </div>
    </div>

    <el-row :gutter="18">
      <el-col :xs="24" :lg="15">
        <el-card shadow="never" class="graph-card">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>ECharts 关系图</strong>
                <small>用户、兴趣、目的地、游记、美食和设施的演示链路</small>
              </div>
              <el-tag effect="plain">真实接口结果生成</el-tag>
            </div>
          </template>
          <div ref="graphRef" class="demo-graph"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="9">
        <el-card shadow="never" class="assistant-card">
          <template #header>算法助手</template>
          <div class="assistant-copy">
            <h3>{{ assistantTitle }}</h3>
            <p>{{ assistantText }}</p>
          </div>
          <AlgorithmTracePanel :trace="profileAnalysis?.algorithm_trace" title="画像 trace" compact />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="18">
      <el-col v-for="card in demoCards" :key="card.key" :xs="24" :lg="8">
        <el-card shadow="never" class="demo-card">
          <template #header>
            <div class="panel-header">
              <div>
                <strong>{{ card.title }}</strong>
                <small>{{ card.subtitle }}</small>
              </div>
              <el-tag :type="card.ok ? 'success' : 'danger'" effect="plain">
                {{ card.ok ? "OK" : "FAIL" }}
              </el-tag>
            </div>
          </template>
          <div class="demo-items">
            <div v-for="item in card.items" :key="item" class="demo-item">{{ item }}</div>
            <el-empty v-if="card.items.length === 0" description="暂无结果" />
          </div>
          <AlgorithmTracePanel :trace="card.trace" compact />
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import AlgorithmTracePanel from "../components/AlgorithmTracePanel.vue";
import {
  apiGet,
  apiPost,
  type AigcAgentPayload,
  type DiaryListPayload,
  type FoodListPayload,
  type NearbyFacilitiesPayload,
  type RecommendationPayload,
  type RoutePlanPayload,
  type UserProfileAnalysisPayload,
} from "../services/api";
import { authState } from "../services/auth";

interface DemoCard {
  key: string;
  title: string;
  subtitle: string;
  ok: boolean;
  items: string[];
  trace: Record<string, unknown>;
}

const loading = ref(false);
const profileLoading = ref(false);
const graphRef = ref<HTMLDivElement | null>(null);
const chart = ref<echarts.ECharts | null>(null);
const demoCards = ref<DemoCard[]>([]);
const profileAnalysis = ref<UserProfileAnalysisPayload | null>(null);
const dashboard = reactive({
  destinations: 0,
  buptRoads: 0,
  summerRoads: 0,
});
const userId = computed(() => authState.user?.id ?? 1);
const assistantTitle = computed(() =>
  profileAnalysis.value?.tags?.length ? "画像已参与推荐权重" : "画像尚未提取",
);
const assistantText = computed(() => {
  if (!profileAnalysis.value?.tags?.length) {
    return "点击刷新 AI 画像后，系统会从收藏、评分和浏览行为中提取兴趣标签，并写回 user_interests 表。";
  }
  return `当前兴趣标签：${profileAnalysis.value.tags.join("、")}。推荐接口会在 interest/composite 策略中读取这些标签。`;
});

async function loadDemo() {
  loading.value = true;
  try {
    const [destinations, buptMap, summerMap, profile, recommendations, route, facilities, diaries, foods, aigc] =
      await Promise.allSettled([
        apiGet<{ total: number; algorithm_trace?: Record<string, string> }>("/api/v1/destinations?limit=1"),
        apiGet<Record<string, number>>("/api/v1/map/stats?scene_key=bupt_shahe"),
        apiGet<Record<string, number>>("/api/v1/map/stats?scene_key=summer_palace"),
        apiGet<UserProfileAnalysisPayload>(`/api/v1/users/${userId.value}/profile/analysis`),
        apiGet<RecommendationPayload>(`/api/v1/recommendations?user_id=${userId.value}&strategy=composite&limit=5`),
        apiPost<RoutePlanPayload>("/api/v1/routes/plan", {
          scene_key: "bupt_shahe",
          start_lng: 116.28333,
          start_lat: 40.15608,
          end_lng: 116.2862,
          end_lat: 40.1582,
          route_source: "local_graph",
          mode: "walk",
        }),
        apiGet<NearbyFacilitiesPayload>("/api/v1/facilities/nearby?scene_key=bupt_shahe&limit=5&radius=900"),
        apiGet<DiaryListPayload>(`/api/v1/diaries/recommend?user_id=${userId.value}&limit=5`),
        apiGet<FoodListPayload>("/api/v1/foods/recommend?destination_id=1&limit=5"),
        apiPost<AigcAgentPayload>("/api/v1/aigc/agent/run", {
          task: "diary_animation",
          text: "颐和园半日游，从东宫门进入，沿昆明湖步道游览，再到佛香阁附近拍摄湖面和古建。",
          destination_name: "颐和园",
          media_urls: ["/media/demo/scenic-photo.jpg"],
          scene_count: 4,
          user_id: userId.value,
        }),
      ]);

    if (destinations.status === "fulfilled") dashboard.destinations = destinations.value.total;
    if (buptMap.status === "fulfilled") dashboard.buptRoads = buptMap.value.roads ?? 0;
    if (summerMap.status === "fulfilled") dashboard.summerRoads = summerMap.value.roads ?? 0;
    if (profile.status === "fulfilled") profileAnalysis.value = profile.value;

    demoCards.value = [
      buildCard("recommend", "景点/学校推荐", "Top-K 堆 + 兴趣权重", recommendations, (payload) =>
        payload.items.map((item) => `${item.name} · ${item.reason ?? "综合排序"}`),
      ),
      buildCard("route", "路线规划", "Dijkstra 本地图路径", route, (payload) => [
        `${Math.round(payload.distance)}m · ${Math.round(payload.duration / 60)} 分钟`,
        ...payload.steps.slice(0, 4).map((item) => item.text),
      ]),
      buildCard("facilities", "附近设施", "Dijkstra 真实路网距离", facilities, (payload) =>
        payload.items.map((item) => `${item.name} · ${Math.round(item.distance ?? 0)}m`),
      ),
      buildCard("diaries", "游记社区", "全文索引 + 热度评分排序", diaries, (payload) =>
        payload.items.map((item) => `${item.title} · ${item.views} 浏览`),
      ),
      buildCard("foods", "美食推荐", "菜系过滤 + Top-K 综合分", foods, (payload) =>
        payload.items.map((item) => `${item.restaurant_name} · ${item.name}`),
      ),
      buildCard("aigc", "AIGC Agent", "工具链 trace + 模拟视频", aigc, (payload) => [
        payload.result.title,
        `步骤 ${payload.agent_trace.steps.length} · ${payload.result.simulated_video_url}`,
      ]),
      buildProfileCard(profile),
      buildMapCard("bupt", "北邮校内图", "道路/建筑/设施数据", buptMap),
      buildMapCard("summer", "颐和园内部图", "景区内部导航数据", summerMap),
    ];
    await nextTick();
    renderGraph();
  } finally {
    loading.value = false;
  }
}

async function extractProfile() {
  profileLoading.value = true;
  try {
    profileAnalysis.value = await apiPost<UserProfileAnalysisPayload>(
      `/api/v1/users/${userId.value}/profile/llm-extract`,
      {},
    );
    ElMessage.success("AI 画像已刷新");
    await loadDemo();
  } finally {
    profileLoading.value = false;
  }
}

function buildCard<T extends { algorithm_trace?: Record<string, unknown> }>(
  key: string,
  title: string,
  subtitle: string,
  result: PromiseSettledResult<T>,
  itemMapper: (payload: T) => string[],
): DemoCard {
  if (result.status === "rejected") {
    return {
      key,
      title,
      subtitle,
      ok: false,
      items: [formatError(result.reason)],
      trace: { stage: "stage-43-demo", status: "failed", error: formatError(result.reason) },
    };
  }
  return {
    key,
    title,
    subtitle,
    ok: true,
    items: itemMapper(result.value).slice(0, 5),
    trace: result.value.algorithm_trace ?? { stage: "stage-43-demo", status: "no_trace" },
  };
}

function buildProfileCard(result: PromiseSettledResult<UserProfileAnalysisPayload>): DemoCard {
  if (result.status === "rejected") {
    return {
      key: "profile",
      title: "LLM 用户画像",
      subtitle: "行为证据 -> 兴趣标签",
      ok: false,
      items: [formatError(result.reason)],
      trace: { stage: "stage-43-llm-user-profile", status: "failed" },
    };
  }
  return {
    key: "profile",
    title: "LLM 用户画像",
    subtitle: "行为证据 -> 兴趣标签",
    ok: true,
    items: [result.value.summary, ...result.value.tags.map((tag) => `${tag}: ${result.value.weights[tag] ?? 0}`)],
    trace: result.value.algorithm_trace,
  };
}

function buildMapCard(
  key: string,
  title: string,
  subtitle: string,
  result: PromiseSettledResult<Record<string, number>>,
): DemoCard {
  if (result.status === "rejected") {
    return {
      key,
      title,
      subtitle,
      ok: false,
      items: [formatError(result.reason)],
      trace: { stage: "stage-43-demo-map-stats", status: "failed" },
    };
  }
  return {
    key,
    title,
    subtitle,
    ok: true,
    items: [
      `节点 ${result.value.nodes ?? 0}`,
      `道路 ${result.value.roads ?? 0}`,
      `建筑 ${result.value.buildings ?? 0}`,
      `设施 ${result.value.facilities ?? 0}`,
    ],
    trace: { stage: "stage-43-demo-map-stats", source: "map/stats", ...result.value },
  };
}

function renderGraph() {
  if (!graphRef.value) return;
  if (!chart.value) {
    chart.value = echarts.init(graphRef.value);
  }
  const categories = [
    { name: "用户" },
    { name: "算法" },
    { name: "内容" },
    { name: "数据" },
  ];
  const nodes = [
    { name: authState.user?.nickname ?? "演示用户", category: 0, symbolSize: 54 },
    { name: "LLM 画像", category: 1, symbolSize: 44 },
    { name: "Top-K 推荐", category: 1, symbolSize: 44 },
    { name: "Dijkstra 路距", category: 1, symbolSize: 44 },
    { name: "Huffman/索引", category: 1, symbolSize: 44 },
    { name: "AIGC Agent", category: 1, symbolSize: 44 },
    { name: "景点/学校", category: 2, symbolSize: 42 },
    { name: "附近设施", category: 2, symbolSize: 42 },
    { name: "游记", category: 2, symbolSize: 42 },
    { name: "美食", category: 2, symbolSize: 42 },
    { name: "北邮路网", category: 3, symbolSize: 40 },
    { name: "颐和园路网", category: 3, symbolSize: 40 },
  ];
  const links = [
    ["演示用户", "LLM 画像"],
    ["LLM 画像", "Top-K 推荐"],
    ["Top-K 推荐", "景点/学校"],
    ["Dijkstra 路距", "附近设施"],
    ["Huffman/索引", "游记"],
    ["AIGC Agent", "游记"],
    ["Top-K 推荐", "美食"],
    ["北邮路网", "Dijkstra 路距"],
    ["颐和园路网", "Dijkstra 路距"],
    ["景点/学校", "游记"],
    ["景点/学校", "美食"],
  ].map(([source, target]) => ({ source: source === "演示用户" ? authState.user?.nickname ?? "演示用户" : source, target }));

  chart.value.setOption({
    tooltip: {},
    legend: [{ data: categories.map((item) => item.name), bottom: 0 }],
    series: [
      {
        type: "graph",
        layout: "force",
        categories,
        roam: true,
        draggable: true,
        label: { show: true, color: "#17202a", fontSize: 12 },
        force: { repulsion: 220, edgeLength: 120 },
        data: nodes,
        links,
        lineStyle: { color: "#98a2b3", width: 1.5, curveness: 0.16 },
      },
    ],
  });
}

function formatError(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function resizeGraph() {
  chart.value?.resize();
}

onMounted(async () => {
  await loadDemo();
  window.addEventListener("resize", resizeGraph);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeGraph);
  chart.value?.dispose();
});
</script>

<style scoped>
.demo-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(360px, 0.9fr);
  gap: 18px;
  align-items: stretch;
  padding: 22px;
  border: 1px solid #d6ebe7;
  border-radius: 8px;
  background: linear-gradient(135deg, #ffffff, #f0faf8);
}

.hero-kicker {
  color: #0f766e;
  font-weight: 800;
}

.demo-hero h2 {
  margin: 8px 0;
  color: #101828;
  font-size: 28px;
  letter-spacing: 0;
}

.demo-hero p {
  max-width: 760px;
  margin: 0;
  color: #667085;
  line-height: 1.7;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.hero-metrics div {
  padding: 14px;
  border: 1px solid #d6ebe7;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
}

.hero-metrics span,
.panel-header small {
  display: block;
  color: #667085;
  font-size: 12px;
}

.hero-metrics strong {
  display: block;
  margin-top: 6px;
  color: #101828;
  font-size: 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.demo-graph {
  width: 100%;
  height: 430px;
}

.assistant-card {
  min-height: 520px;
}

.assistant-copy {
  margin-bottom: 16px;
  padding: 14px;
  border-radius: 8px;
  background: #f9fafb;
}

.assistant-copy h3 {
  margin: 0 0 8px;
  color: #101828;
}

.assistant-copy p {
  margin: 0;
  color: #667085;
  line-height: 1.65;
}

.demo-card {
  min-height: 360px;
}

.demo-items {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
}

.demo-item {
  overflow: hidden;
  padding: 9px 10px;
  border: 1px solid #edf1f5;
  border-radius: 8px;
  background: #fcfcfd;
  color: #475467;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
