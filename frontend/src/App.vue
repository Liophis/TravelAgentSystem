<template>
  <router-view v-if="$route.path === '/login'" />
  <el-container v-else class="app-shell">
    <el-aside width="252px" class="app-sidebar">
      <div class="brand">
        <span class="brand-mark">游</span>
        <div>
          <strong>Smart Tour Guide</strong>
          <small>算法旅游服务平台</small>
        </div>
      </div>
      <el-menu router :default-active="$route.path" class="nav-menu">
        <el-menu-item v-for="item in visibleNavItems" :key="item.path" :index="item.path">
          <span class="nav-kicker">{{ item.kicker }}</span>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div>
          <strong>{{ currentNavItem?.label ?? "总览" }}</strong>
          <span>{{ currentNavItem?.description ?? "多场景旅游算法服务平台" }}</span>
        </div>
        <div class="account-bar">
          <span class="status-pill">SQLite Dev · AMap</span>
          <el-tag v-if="authState.user" :type="authState.role === 'admin' ? 'warning' : 'success'">
            {{ authState.user.nickname }} · {{ roleLabel(authState.role) }}
          </el-tag>
          <el-button size="small" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { authState, clearAuth, isAdmin } from "./services/auth";

const route = useRoute();
const router = useRouter();
const navItems = [
  { path: "/", label: "总览", kicker: "01", description: "服务入口与项目能力总览" },
  { path: "/profile", label: "个人偏好", kicker: "02", description: "用户画像、兴趣和行为反馈" },
  { path: "/map", label: "地图与目的地", kicker: "03", description: "全国目的地 POI 与内部地图图层" },
  { path: "/routes", label: "路线规划", kicker: "04", description: "北邮沙河与颐和园内部导航" },
  { path: "/indoor", label: "室内导航", kicker: "05", description: "楼宇内跨楼层路线规划" },
  { path: "/facilities", label: "附近设施", kicker: "06", description: "按真实道路距离查找设施" },
  { path: "/diaries", label: "游记社区", kicker: "07", description: "游记列表、查询、浏览、评分和评论" },
  { path: "/diaries/create", label: "发布与 AIGC", kicker: "08", description: "发布游记并生成 Agent 分镜和模拟视频" },
  { path: "/foods", label: "美食推荐", kicker: "09", description: "美食检索、推荐和路线预览" },
  { path: "/admin", label: "管理后台", kicker: "10", description: "数据看板与内容管理", adminOnly: true },
];

const visibleNavItems = computed(() => navItems.filter((item) => !item.adminOnly || isAdmin()));
const currentNavItem = computed(
  () =>
    visibleNavItems.value
      .slice()
      .sort((left, right) => right.path.length - left.path.length)
      .find((item) => route.path === item.path || route.path.startsWith(`${item.path}/`)),
);

function roleLabel(role: string) {
  return role === "admin" ? "管理员" : "普通用户";
}

async function logout() {
  clearAuth();
  await router.replace("/login");
}
</script>
