import axios from 'axios'
import type { PoiSummary, RouteHop, TripChatRequest, TripChatResponse, TripPlanResponse } from '@/types'

const apiBase = import.meta.env.VITE_API_BASE_URL ?? ''

const http = axios.create({
  baseURL: apiBase,
  timeout: 30000,
})

export const listPois = async (params?: { skip?: number; limit?: number }) => {
  const response = await http.get<PoiSummary[]>('/api/pois', { params })
  return response.data
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

export const generateDemoPlan = async (): Promise<TripPlanResponse> => {
  try {
    // Try backend-generated plan using default demo params
    const params = {
      city: 'Tokyo',
      start_date: '2026-05-01',
      end_date: '2026-05-03',
      travel_days: 3,
    }
    const res = await http.post('/api/trips', null, { params })
    return res.data as TripPlanResponse
  } catch (err) {
    // fallback local demo
    return {
      success: true,
      message: 'demo',
      data: {
        city: 'Tokyo',
        start_date: '2026-05-01',
        end_date: '2026-05-03',
        overall_suggestions: 'This is a demo itinerary scaffold. Connect your backend generator here.',
        weather_info: [],
        budget: {
          total_attractions: 1200,
          total_hotels: 1800,
          total_meals: 900,
          total_transportation: 300,
          total: 4200,
        },
        days: [
          {
            date: '2026-05-01',
            day_index: 0,
            description: 'Arrival and city orientation',
            transportation: 'Mixed',
            accommodation: 'Comfort hotel',
            attractions: [],
            meals: [],
          },
        ],
      },
    }
  }
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
