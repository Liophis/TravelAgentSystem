<template>
  <section class="page-stack">
    <div class="page-heading">
      <div>
        <h1>室内导航</h1>
        <p>教学楼室内节点图，支持大门、电梯、楼梯、楼层和房间路径。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="planRoute">规划室内路线</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="7">
        <el-card shadow="never">
          <el-form label-position="top">
            <el-form-item label="建筑">
              <el-select v-model="buildingName" @change="loadNodes">
                <el-option
                  v-for="building in buildings"
                  :key="building.building_name"
                  :label="building.building_name"
                  :value="building.building_name"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="起点">
              <el-select v-model="startNodeId" filterable>
                <el-option
                  v-for="node in nodes"
                  :key="node.id"
                  :label="nodeLabel(node)"
                  :value="node.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="终点">
              <el-select v-model="endNodeId" filterable>
                <el-option
                  v-for="node in nodes"
                  :key="node.id"
                  :label="nodeLabel(node)"
                  :value="node.id"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="route" shadow="never" class="result-card">
          <div class="stat"><span>总距离</span><strong>{{ route.distance }} m</strong></div>
          <div class="stat"><span>预计时间</span><strong>{{ Math.round(route.duration) }} s</strong></div>
          <el-timeline>
            <el-timeline-item v-for="step in route.steps" :key="`${step.from_node_id}-${step.to_node_id}`">
              {{ step.text }} · {{ step.distance }} m
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :span="17">
        <el-card shadow="never">
          <el-tabs v-model="activeFloor">
            <el-tab-pane
              v-for="floor in floors"
              :key="floor"
              :label="`${floor} 层`"
              :name="String(floor)"
            >
              <div class="floor-plan">
                <div
                  v-for="node in nodesByFloor(floor)"
                  :key="node.id"
                  class="indoor-node"
                  :class="{ active: routeNodeIds.has(node.id) }"
                  :style="{ left: `${node.x}%`, top: `${node.y + 36}%` }"
                >
                  <span>{{ node.name }}</span>
                  <small>{{ node.node_type }}</small>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { apiGet, apiPost, type IndoorBuildingItem, type IndoorNodeItem, type IndoorRoutePayload } from "../services/api";

const loading = ref(false);
const buildings = ref<IndoorBuildingItem[]>([]);
const nodes = ref<IndoorNodeItem[]>([]);
const route = ref<IndoorRoutePayload | null>(null);
const buildingName = ref("综合教学楼");
const startNodeId = ref<number | null>(null);
const endNodeId = ref<number | null>(null);
const activeFloor = ref("1");

const floors = computed(() => {
  const current = buildings.value.find((building) => building.building_name === buildingName.value);
  return current?.floors ?? [1];
});

const routeNodeIds = computed(() => new Set(route.value?.path.map((node) => node.id) ?? []));

async function loadBuildings() {
  const payload = await apiGet<{ items: IndoorBuildingItem[] }>("/api/v1/indoor/buildings");
  buildings.value = payload.items;
  buildingName.value = payload.items[0]?.building_name ?? buildingName.value;
}

async function loadNodes() {
  const params = new URLSearchParams({ building_name: buildingName.value });
  const payload = await apiGet<{ items: IndoorNodeItem[] }>(`/api/v1/indoor/nodes?${params}`);
  nodes.value = payload.items;
  startNodeId.value = nodes.value.find((node) => node.node_type === "entrance")?.id ?? nodes.value[0]?.id ?? null;
  endNodeId.value = nodes.value.find((node) => node.name.includes("305"))?.id ?? nodes.value.at(-1)?.id ?? null;
  activeFloor.value = String(floors.value[0] ?? 1);
}

async function planRoute() {
  if (!startNodeId.value || !endNodeId.value) return;
  loading.value = true;
  try {
    route.value = await apiPost<IndoorRoutePayload>("/api/v1/indoor/routes", {
      building_name: buildingName.value,
      start_node_id: startNodeId.value,
      end_node_id: endNodeId.value,
    });
    activeFloor.value = String(route.value.end.floor);
  } finally {
    loading.value = false;
  }
}

function nodesByFloor(floor: number) {
  return nodes.value.filter((node) => node.floor === floor);
}

function nodeLabel(node: IndoorNodeItem) {
  return `${node.floor} 层 · ${node.name}`;
}

onMounted(async () => {
  await loadBuildings();
  await loadNodes();
  await planRoute();
});
</script>

<style scoped>
.floor-plan {
  position: relative;
  min-height: 420px;
  border: 1px solid #d7dde8;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.14) 1px, transparent 1px),
    linear-gradient(rgba(148, 163, 184, 0.14) 1px, transparent 1px);
  background-size: 48px 48px;
}

.indoor-node {
  position: absolute;
  width: 112px;
  min-height: 48px;
  transform: translate(-50%, -50%);
  border: 1px solid #b8c2d4;
  background: #ffffff;
  padding: 6px 8px;
  box-sizing: border-box;
  text-align: center;
  font-size: 12px;
}

.indoor-node span,
.indoor-node small {
  display: block;
  overflow-wrap: anywhere;
}

.indoor-node small {
  color: #64748b;
  margin-top: 2px;
}

.indoor-node.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
}
</style>
