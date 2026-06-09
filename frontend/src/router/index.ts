import { createRouter, createWebHistory } from "vue-router";

import AdminDashboardPage from "../pages/AdminDashboardPage.vue";
import DiaryCreateAigcPage from "../pages/DiaryCreateAigcPage.vue";
import DiaryCommunityPage from "../pages/DiaryCommunityPage.vue";
import FoodRecommendPage from "../pages/FoodRecommendPage.vue";
import HomePage from "../pages/HomePage.vue";
import IndoorNavigationPage from "../pages/IndoorNavigationPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import MapGuidePage from "../pages/MapGuidePage.vue";
import NearbyFacilitiesPage from "../pages/NearbyFacilitiesPage.vue";
import RoutePlannerPage from "../pages/RoutePlannerPage.vue";
import UserPreferencePage from "../pages/UserPreferencePage.vue";
import { authState, isAdmin } from "../services/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginPage },
    { path: "/", name: "home", component: HomePage },
    { path: "/destinations", redirect: "/map" },
    { path: "/profile", name: "profile", component: UserPreferencePage },
    { path: "/map", name: "map-guide", component: MapGuidePage },
    { path: "/routes", name: "route-planner", component: RoutePlannerPage },
    { path: "/indoor", name: "indoor-navigation", component: IndoorNavigationPage },
    { path: "/facilities", name: "nearby-facilities", component: NearbyFacilitiesPage },
    { path: "/diaries", name: "diaries", component: DiaryCommunityPage },
    { path: "/diaries/create", name: "diary-create-aigc", component: DiaryCreateAigcPage },
    { path: "/foods", name: "foods", component: FoodRecommendPage },
    { path: "/aigc", redirect: "/diaries/create" },
    { path: "/admin", name: "admin", component: AdminDashboardPage, meta: { requiresAdmin: true } },
  ],
});

router.beforeEach((to) => {
  if (to.name !== "login" && !authState.token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.name === "login" && authState.token) {
    return "/";
  }
  if (to.meta.requiresAdmin && !isAdmin()) {
    return "/";
  }
  return true;
});

export default router;
