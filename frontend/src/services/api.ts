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
}

export interface MapGeoJsonPayload {
  center: Coordinate;
  statistics: {
    roads: number;
    buildings: number;
    facilities: number;
    categories: number;
  };
  roads: RoadItem[];
  buildings: BuildingItem[];
  facilities: FacilityItem[];
  facility_categories: string[];
  source: string;
}

export interface RoutePlanPayload {
  strategy: string;
  mode: string;
  distance: number;
  duration: number;
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
