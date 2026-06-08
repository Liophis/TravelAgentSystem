<template>
  <el-container class="app-shell">
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
          <span>{{ currentNavItem?.description ?? "景点/学校推荐 + 多场景内部导航平台" }}</span>
        </div>
        <span class="status-pill">SQLite Dev · AMap</span>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { isAdmin } from "./services/auth";

const route = useRoute();
const navItems = [
  { path: "/", label: "总览", kicker: "01", description: "项目能力总览与推荐预览" },
  { path: "/profile", label: "个人偏好", kicker: "02", description: "用户画像、登录和行为反馈" },
  { path: "/destinations", label: "景点/学校", kicker: "03", description: "全国目的地检索与排序" },
  { path: "/map", label: "地图导览", kicker: "04", description: "多场景道路、建筑和设施图层" },
  { path: "/routes", label: "路线规划", kicker: "05", description: "北邮沙河与颐和园内部导航" },
  { path: "/indoor", label: "室内导航", kicker: "06", description: "楼宇内跨楼层路线规划" },
  { path: "/facilities", label: "附近设施", kicker: "07", description: "按真实道路距离查找设施" },
  { path: "/diaries", label: "游记社区", kicker: "08", description: "游记管理、检索、评分和交流" },
  { path: "/foods", label: "美食推荐", kicker: "09", description: "美食检索、推荐和路线预览" },
  { path: "/aigc", label: "AIGC 辅助", kicker: "10", description: "Agent 式游记动画工作流" },
  { path: "/admin", label: "管理后台", kicker: "11", description: "数据看板与内容管理", adminOnly: true },
];

const visibleNavItems = computed(() => navItems.filter((item) => !item.adminOnly || isAdmin()));
const currentNavItem = computed(() => visibleNavItems.value.find((item) => item.path === route.path));
</script>
