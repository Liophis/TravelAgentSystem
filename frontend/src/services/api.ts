import axios from 'axios'
import type {
  PoiSummary,
  RouteHop,
  RuntimeSettings,
  RuntimeSettingsResponse,
  TripChatRequest,
  TripChatResponse,
  TripPlanResponse,
  XHSContentSourceResponse,
} from '@/types'

const apiBase = import.meta.env.VITE_API_BASE_URL ?? ''
const apiBaseStorageKey = 'travelagent.runtime.api_base_url'
const mapJsKeyStorageKey = 'travelagent.runtime.amap_web_js_key'

const normalizeText = (value: unknown): string => String(value ?? '').trim()
const normalizeBaseUrl = (value: string | null | undefined): string => normalizeText(value).replace(/\/+$/, '')

const resolveDefaultApiBaseUrl = (): string => {
  const fromEnv = normalizeBaseUrl(apiBase)
  if (fromEnv) return fromEnv
  return 'http://localhost:8000'
}

const DEFAULT_API_BASE_URL = resolveDefaultApiBaseUrl()
const DEFAULT_AMAP_WEB_JS_KEY = normalizeText(import.meta.env.VITE_AMAP_WEB_JS_KEY ?? '')

export const getRuntimeApiBaseUrl = (): string => {
  if (typeof window === 'undefined') return DEFAULT_API_BASE_URL
  const saved = normalizeBaseUrl(window.localStorage.getItem(apiBaseStorageKey))
  return saved || DEFAULT_API_BASE_URL
}

export const setRuntimeApiBaseUrl = (value: string): string => {
  const normalized = normalizeBaseUrl(value) || DEFAULT_API_BASE_URL
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(apiBaseStorageKey, normalized)
  }
  return normalized
}

export const getRuntimeMapJsKey = (): string => {
  if (typeof window === 'undefined') return DEFAULT_AMAP_WEB_JS_KEY
  const saved = normalizeText(window.localStorage.getItem(mapJsKeyStorageKey))
  return saved || DEFAULT_AMAP_WEB_JS_KEY
}

export const setRuntimeMapJsKey = (value: string): string => {
  const normalized = normalizeText(value)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(mapJsKeyStorageKey, normalized)
  }
  return normalized
}

const emitRuntimeSettingsUpdated = () => {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('travelagent:runtime-settings-updated'))
}

const http = axios.create({
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  config.baseURL = getRuntimeApiBaseUrl()
  return config
})

const normalizeRuntimeSettings = (data?: Partial<RuntimeSettings>): RuntimeSettings => ({
  api_base_url: normalizeBaseUrl(data?.api_base_url) || getRuntimeApiBaseUrl(),
  amap_web_api_key: normalizeText(data?.amap_web_api_key),
  vite_amap_web_js_key: normalizeText(data?.vite_amap_web_js_key),
  google_maps_api_key: normalizeText(data?.google_maps_api_key),
  google_maps_proxy: normalizeText(data?.google_maps_proxy),
  xhs_cookie: normalizeText(data?.xhs_cookie),
  xhs_sample_notes_path: normalizeText(data?.xhs_sample_notes_path),
  openai_api_key: normalizeText(data?.openai_api_key),
  openai_base_url: normalizeText(data?.openai_base_url),
  openai_model: normalizeText(data?.openai_model),
  log_level: normalizeText(data?.log_level),
})

export const getRuntimeSettings = async (): Promise<RuntimeSettings> => {
  const response = await http.get<RuntimeSettingsResponse>('/api/settings')
  const settings = normalizeRuntimeSettings(response.data?.data)
  setRuntimeApiBaseUrl(settings.api_base_url)
  if (settings.vite_amap_web_js_key) {
    setRuntimeMapJsKey(settings.vite_amap_web_js_key)
  }
  return settings
}

export const saveRuntimeSettings = async (settings: RuntimeSettings): Promise<RuntimeSettings> => {
  const previousBaseUrl = getRuntimeApiBaseUrl()
  const targetBaseUrl = normalizeBaseUrl(settings.api_base_url) || previousBaseUrl

  try {
    const response = await http.put<RuntimeSettingsResponse>('/api/settings', {
      api_base_url: settings.api_base_url,
      amap_web_api_key: settings.amap_web_api_key,
      vite_amap_web_js_key: settings.vite_amap_web_js_key,
      google_maps_api_key: settings.google_maps_api_key,
      google_maps_proxy: settings.google_maps_proxy,
      xhs_cookie: settings.xhs_cookie,
      xhs_sample_notes_path: settings.xhs_sample_notes_path,
      openai_api_key: settings.openai_api_key,
      openai_base_url: settings.openai_base_url,
      openai_model: settings.openai_model,
      log_level: settings.log_level,
    }, { baseURL: previousBaseUrl })

    const saved = normalizeRuntimeSettings(response.data?.data)
    setRuntimeApiBaseUrl(targetBaseUrl)
    setRuntimeMapJsKey(saved.vite_amap_web_js_key || settings.vite_amap_web_js_key)
    emitRuntimeSettingsUpdated()
    return saved
  } catch (error) {
    setRuntimeApiBaseUrl(previousBaseUrl)
    throw error
  }
}

export const listPois = async (params?: { skip?: number; limit?: number }) => {
  const response = await http.get<PoiSummary[]>('/api/pois', { params })
  const data: any = response.data
  return Array.isArray(data) ? data : (data?.items ?? [])
}

export const searchPois = async (keyword: string, limit = 10) => {
  const response = await http.get<PoiSummary[]>('/api/pois/search', {
    params: { keyword, limit },
  })
  return response.data
}

export const getPoi = async (poiId: number) => {
  const response = await http.get<PoiSummary>(`/api/pois/${poiId}`)
  return response.data
}

export const createPoi = async (payload: PoiSummary) => {
  const response = await http.post<PoiSummary>('/api/pois', payload)
  return response.data
}

export const findRoute = async (startPoiId: number, endPoiId: number) => {
  const response = await http.get<RouteHop[]>(`/api/routes/${startPoiId}/${endPoiId}`)
  return response.data
}

export const createUser = async (payload: { username: string; email: string; interests?: string }) => {
  const response = await http.post('/api/users', payload)
  return response.data
}

export const generateTrip = async (payload: {
  city: string
  start_date: string
  end_date: string
  travel_days?: number
  transportation?: string
  accommodation?: string
  preferences?: string[]
  free_text_input?: string
}) => {
  const res = await http.post('/api/trips', null, { params: payload })
  return res.data as TripPlanResponse
}

export const askTripChat = async (payload: TripChatRequest) => {
  const response = await http.post<TripChatResponse>('/api/chat/ask', payload)
  return response.data
}

export const getXhsContentSourceStatus = async () => {
  const response = await http.get<XHSContentSourceResponse>('/api/xhs/content-source')
  return response.data
}

export const importXhsContentSource = async (payload: { source_name?: string; notes: object[] }) => {
  const response = await http.post<XHSContentSourceResponse>('/api/xhs/content-source/import', payload)
  return response.data
}

export const clearXhsContentSourceImport = async () => {
  const response = await http.delete<XHSContentSourceResponse>('/api/xhs/content-source/import')
  return response.data
}
