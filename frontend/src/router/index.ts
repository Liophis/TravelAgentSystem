import { createRouter, createWebHistory } from "vue-router";

import DestinationListPage from "../pages/DestinationListPage.vue";
import DiaryCommunityPage from "../pages/DiaryCommunityPage.vue";
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
  ],
});

export default router;
