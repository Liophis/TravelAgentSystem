import { ElMessage } from "element-plus";

export type Coordinate = [number, number];

export interface FacilityItem {
  id: string;
  name: string;
  category: string;
  category_name?: string;
  lng: number;
  lat: number;
  description?: string;
  distance?: number;
  duration?: number;
  routePath?: Coordinate[];
  node_ids?: number[];
}

export interface BuildingItem {
  id: string;
  name: string;
  polygon: Coordinate[];
}

export interface RoadItem {
  id: string;
  path: Coordinate[];
  congestion?: number;
  allowed_modes?: string[];
}

export interface RouteEndpointItem {
  id: string;
  source: string;
  name: string;
  lng: number;
  lat: number;
}

export interface MapGeoJsonPayload {
  center: Coordinate;
  statistics: {
    roads: number;
    buildings: number;
    facilities: number;
    categories: number;
    hidden_demo_roads?: number;
    hidden_demo_buildings?: number;
    hidden_demo_facilities?: number;
  };
  roads: RoadItem[];
  buildings: BuildingItem[];
  facilities: FacilityItem[];
  facility_categories: string[];
  source: string;
  layer_policy?: Record<string, unknown>;
}

export interface RoutePlanPayload {
  strategy: string;
  mode: string;
  route_source?: string;
  distance: number;
  duration: number;
  start?: RouteEndpointItem;
  end?: RouteEndpointItem;
  path: Coordinate[];
  node_ids?: number[];
  steps: Array<{ text: string; distance: number }>;
  visit_order?: Array<{ index: number; name: string; lng: number; lat: number }>;
  segments?: Array<{
    from: string;
    to: string;
    distance: number;
    duration: number;
    path: Coordinate[];
    node_ids?: number[];
  }>;
  algorithm_trace: Record<string, string>;
}

export interface IndoorBuildingItem {
  building_name: string;
  floors: number[];
}

export interface IndoorNodeItem {
  id: number;
  building_name: string;
  floor: number;
  name: string;
  node_type: string;
  x: number;
  y: number;
}

export interface IndoorRoutePayload {
  building_name: string;
  start: IndoorNodeItem;
  end: IndoorNodeItem;
  distance: number;
  duration: number;
  path: IndoorNodeItem[];
  steps: Array<{
    text: string;
    from_node_id: number;
    to_node_id: number;
    floor: number;
    distance: number;
    duration: number;
    access_type: string;
  }>;
  algorithm_trace: Record<string, string>;
}

export interface NearbyFacilitiesPayload {
  items: FacilityItem[];
  total: number;
  category: string | null;
  radius: number;
  algorithm_trace?: Record<string, string>;
}

export interface DestinationItem {
  id: number;
  name: string;
  category: string;
  description: string;
  lng: number;
  lat: number;
  rating: number;
  popularity: number;
  tags: string[];
  score?: number;
  behavior_score?: number;
  reason?: string;
}

export interface DestinationListPayload {
  items: DestinationItem[];
  total: number;
  limit: number;
  offset: number;
  categories: string[];
  algorithm_trace?: Record<string, string>;
}

export interface RecommendationPayload {
  items: DestinationItem[];
  total: number;
  strategy: string;
  user_id: number | null;
  algorithm_trace: Record<string, string>;
}

export interface UserTargetRef {
  id: number;
  user_id: number;
  target_type: string;
  target_id: number;
  target_name?: string | null;
}

export interface UserFavoriteItem extends UserTargetRef {
  note?: string | null;
  created_at: string;
}

export interface UserRatingItem extends UserTargetRef {
  rating: number;
  aggregate_rating?: number | null;
  created_at: string;
  updated_at: string;
}

export interface UserBehaviorItem extends UserTargetRef {
  action: string;
  metadata_text?: string | null;
  created_at: string;
}

export interface UserProfileItem {
  id: number;
  username: string;
  email: string;
  nickname: string;
  avatar_url: string | null;
  interests: string[];
  favorites?: UserFavoriteItem[];
  ratings?: UserRatingItem[];
  recent_behaviors?: UserBehaviorItem[];
}

export interface UserListPayload {
  items: UserProfileItem[];
  total: number;
  available_interests: string[];
  algorithm_trace: Record<string, string>;
}

export interface UserProfilePayload extends UserProfileItem {
  available_interests: string[];
  algorithm_trace: Record<string, string>;
}

export interface AuthPayload {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: UserProfileItem;
  algorithm_trace: Record<string, string>;
}

export interface SearchPlaceItem {
  id: string;
  source: string;
  source_id: number;
  name: string;
  category: string;
  lng: number;
  lat: number;
  description?: string;
}

export interface SearchPlacesPayload {
  items: SearchPlaceItem[];
  total: number;
  keyword: string;
  category: string | null;
  algorithm_trace: Record<string, string>;
}

export interface DiaryCommentItem {
  id: number;
  diary_id: number;
  user_id: number;
  content: string;
  created_at: string;
}

export interface DiaryMediaItem {
  id: number;
  diary_id: number;
  media_type: string;
  url: string;
  caption?: string | null;
  created_at: string;
}

export interface DiaryItem {
  id: number;
  user_id: number;
  destination_id: number | null;
  title: string;
  summary: string;
  body?: string;
  views: number;
  rating_avg: number;
  rating_count: number;
  created_at: string;
  comments?: DiaryCommentItem[];
  media?: DiaryMediaItem[];
  score?: number;
  reason?: string;
}

export interface DiaryListPayload {
  items: DiaryItem[];
  total: number;
  limit: number;
  offset: number;
  algorithm_trace?: Record<string, string>;
}

export interface DiaryCompressionPayload {
  diary_id: number;
  algorithm: string;
  original_size: number;
  compressed_size: number;
  compression_ratio: number;
  decompress_ok: boolean;
}

export interface RestaurantItem {
  id: number;
  destination_id?: number | null;
  name: string;
  lng: number;
  lat: number;
  heat: number;
  food_count: number;
  cuisines: string[];
}

export interface FoodItem {
  id: number;
  restaurant_id: number;
  restaurant_destination_id?: number | null;
  restaurant_name: string;
  restaurant_lng: number;
  restaurant_lat: number;
  restaurant_heat: number;
  name: string;
  cuisine: string;
  price: number;
  rating: number;
  heat: number;
  score?: number;
  distance?: number;
  duration?: number;
  reason?: string;
  routePath?: Coordinate[];
  node_ids?: number[];
}

export interface RestaurantListPayload {
  items: RestaurantItem[];
  total: number;
  destination_id?: number | null;
  limit: number;
  offset: number;
  algorithm_trace?: Record<string, string>;
}

export interface FoodListPayload {
  items: FoodItem[];
  total: number;
  limit?: number;
  offset?: number;
  cuisines?: string[];
  keyword?: string;
  cuisine?: string | null;
  destination_id?: number | null;
  radius?: number;
  algorithm_trace?: Record<string, string>;
}

export interface AigcDraftPayload {
  title: string;
  draft: string;
  prompt: string;
  algorithm_trace: Record<string, string>;
}

export interface AigcStoryboardPayload {
  scenes: Array<{ index: number; title: string; description: string; duration_seconds: number }>;
  prompt: string;
  simulated_video_url: string;
  algorithm_trace: Record<string, string>;
}

export interface AdminStatsPayload {
  map: Record<string, number>;
  tables: Record<string, number>;
}

export interface AdminDiaryItem {
  id: number;
  user_id: number;
  destination_id: number | null;
  title: string;
  views: number;
  rating_count: number;
  created_at: string;
}

export interface AdminDiaryListPayload {
  items: AdminDiaryItem[];
  total: number;
  limit: number;
  offset: number;
  algorithm_trace: Record<string, string>;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`);
    return await parseResponse<T>(response);
  } catch (error) {
    notifyApiError(error);
    throw error;
  }
}

export async function apiGetWithAuth<T>(path: string, token: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return await parseResponse<T>(response);
  } catch (error) {
    notifyApiError(error);
    throw error;
  }
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await parseResponse<T>(response);
  } catch (error) {
    notifyApiError(error);
    throw error;
  }
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await parseResponse<T>(response);
  } catch (error) {
    notifyApiError(error);
    throw error;
  }
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await parseResponse<T>(response);
  } catch (error) {
    notifyApiError(error);
    throw error;
  }
}

export async function apiDelete<T>(path: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "DELETE",
    });
    return await parseResponse<T>(response);
  } catch (error) {
    notifyApiError(error);
    throw error;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("登录状态已失效，请重新登录。");
    }
    const body = await readErrorBody(response);
    throw new Error(body || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function readErrorBody(response: Response): Promise<string> {
  const text = await response.text();
  try {
    const payload = JSON.parse(text) as { detail?: string };
    return payload.detail ?? text;
  } catch {
    return text;
  }
}

function notifyApiError(error: unknown) {
  const message = error instanceof Error ? error.message : "请求失败，请稍后重试。";
  ElMessage.error(message);
}
