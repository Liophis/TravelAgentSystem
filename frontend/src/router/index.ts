import { createRouter, createWebHistory } from "vue-router";

import AdminDashboardPage from "../pages/AdminDashboardPage.vue";
import AigcAssistantPage from "../pages/AigcAssistantPage.vue";
import DestinationListPage from "../pages/DestinationListPage.vue";
import DiaryCommunityPage from "../pages/DiaryCommunityPage.vue";
import FoodRecommendPage from "../pages/FoodRecommendPage.vue";
import HomePage from "../pages/HomePage.vue";
import MapGuidePage from "../pages/MapGuidePage.vue";
import NearbyFacilitiesPage from "../pages/NearbyFacilitiesPage.vue";
import RoutePlannerPage from "../pages/RoutePlannerPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomePage },
    { path: "/destinations", name: "destinations", component: DestinationListPage },
    { path: "/map", name: "map-guide", component: MapGuidePage },
    { path: "/routes", name: "route-planner", component: RoutePlannerPage },
    { path: "/facilities", name: "nearby-facilities", component: NearbyFacilitiesPage },
    { path: "/diaries", name: "diaries", component: DiaryCommunityPage },
    { path: "/foods", name: "foods", component: FoodRecommendPage },
    { path: "/aigc", name: "aigc", component: AigcAssistantPage },
    { path: "/admin", name: "admin", component: AdminDashboardPage },
  ],
});

export default router;
