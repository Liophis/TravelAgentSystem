export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  id: number
  name: string
  type?: string
  category?: string
  address: string
  location: Location
  latitude?: number
  longitude?: number
  visit_duration: number
  description: string
  rating?: number
  image_url?: string
  ticket_price?: number
  estimated_cost?: number
  content_sources?: ContentSource[]
  recommendation_reasons?: string[]
  travel_notes?: TravelContentNote[]
  dayArrayIndex?: number
}

export interface ContentImage {
  url: string
  alt?: string
}

export interface ContentSource {
  source_type: string
  source_label: string
  origin: 'external' | 'local_sample' | string
}

export interface TravelContentNote {
  id: string
  source_type: string
  source_label: string
  origin: 'external' | 'local_sample' | string
  title: string
  city: string
  poi_name: string
  author?: string
  tags: string[]
  images: ContentImage[]
  highlights: string[]
  cautions: string[]
  excerpt?: string
  match_reason?: string
  note_url?: string
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost?: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range: string
  rating: string
  distance: string
  type: string
  estimated_cost?: number
}

export interface Budget {
  total_attractions: number
  total_hotels: number
  total_meals: number
  total_transportation: number
  total: number
}

export interface RequestSummary {
  city: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
  data_mode: 'city_match' | 'local_sample'
  data_note: string
}

export interface DayPlan {
  date: string
  day_index: number
  description: string
  transportation: string
  accommodation: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
  request_summary?: RequestSummary
  content_sources?: ContentSource[]
  recommendation_reasons?: string[]
}

export interface TripFormData {
  city: string
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
}

export interface TripPlanResponse {
  success: boolean
  message: string
  data?: TripPlan
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface TripChatRequest {
  message: string
  trip_plan: object
  history: ChatMessage[]
}

export interface TripChatResponse {
  success: boolean
  reply: string
}

export interface RuntimeSettings {
  api_base_url: string
  amap_web_api_key: string
  vite_amap_web_js_key: string
  google_maps_api_key: string
  google_maps_proxy: string
  xhs_cookie: string
  xhs_rap_param: string
  xhs_sample_notes_path: string
  openai_api_key: string
  openai_base_url: string
  openai_model: string
  log_level?: string
}

export interface RuntimeSettingsResponse {
  success: boolean
  message: string
  data?: RuntimeSettings
}

export interface XHSContentSourceStatus {
  active_source: 'runtime_import' | 'configured_path' | 'builtin_fallback' | string
  source_name: string
  path: string
  note_count: number
  format_kind: string
  updated_at: string
  uses_builtin_fallback: boolean
}

export interface XHSContentSourceResponse {
  success: boolean
  message: string
  data?: XHSContentSourceStatus
  meta?: {
    query?: string
    raw_note_count?: number
  }
}

export interface XHSRefreshTripResponse {
  success: boolean
  message: string
  data?: TripPlan
  meta?: {
    query?: string
    raw_note_count?: number
    content_source_status?: XHSContentSourceStatus
  }
}

export interface PoiSummary {
  id: number
  name: string
  city: string
  type: string
  latitude: number
  longitude: number
  floor?: number | null
  description?: string | null
}

export interface RouteHop {
  poi_id: number
  name: string
  distance: number
}
