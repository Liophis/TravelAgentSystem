import { createRouter, createWebHistory } from "vue-router";

import HomePage from "../pages/HomePage.vue";
import MapGuidePage from "../pages/MapGuidePage.vue";
import NearbyFacilitiesPage from "../pages/NearbyFacilitiesPage.vue";
import RoutePlannerPage from "../pages/RoutePlannerPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomePage },
    { path: "/map", name: "map-guide", component: MapGuidePage },
    { path: "/routes", name: "route-planner", component: RoutePlannerPage },
    { path: "/facilities", name: "nearby-facilities", component: NearbyFacilitiesPage },
  ],
});

export default router;
