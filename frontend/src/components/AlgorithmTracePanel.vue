<template>
  <section class="trace-panel" :class="{ compact }">
    <div v-if="title" class="trace-title">{{ title }}</div>
    <div v-if="traceEntries.length" class="trace-grid">
      <div v-for="[key, value] in traceEntries" :key="key" class="trace-item">
        <span>{{ key }}</span>
        <strong>{{ formatValue(value) }}</strong>
      </div>
    </div>
    <el-empty v-else description="暂无算法记录" />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    trace?: Record<string, unknown> | null;
    title?: string;
    compact?: boolean;
  }>(),
  {
    trace: null,
    title: "",
    compact: false,
  },
);

const traceEntries = computed(() => Object.entries(props.trace ?? {}).filter(([, value]) => value !== ""));

function formatValue(value: unknown) {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value ?? "-");
}
</script>

<style scoped>
.trace-panel {
  display: grid;
  gap: 12px;
}

.trace-title {
  color: #101828;
  font-weight: 800;
}

.trace-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.trace-panel.compact .trace-grid {
  grid-template-columns: 1fr;
  gap: 8px;
}

.trace-item {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  background: #f9fafb;
}

.trace-item span {
  display: block;
  margin-bottom: 4px;
  color: #667085;
  font-size: 12px;
}

.trace-item strong {
  display: block;
  overflow-wrap: anywhere;
  color: #101828;
  font-size: 13px;
  line-height: 1.45;
}
</style>
