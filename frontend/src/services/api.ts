export type Coordinate = [number, number];

export interface FacilityItem {
  id: string;
  name: string;
  category: string;
  lng: number;
  lat: number;
  description?: string;
  distance?: number;
  duration?: number;
  routePath?: Coordinate[];
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
  distance: number;
  duration: number;
  path: Coordinate[];
  steps: Array<{ text: string; distance: number }>;
  algorithm_trace: Record<string, string>;
}

export interface NearbyFacilitiesPayload {
  items: FacilityItem[];
  total: number;
  category: string | null;
  radius: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseResponse<T>(response);
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}
