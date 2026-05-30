import api from './api'

export interface Sport {
  id: number
  name: string
  slug: string
}

export interface Selection {
  id: number
  name: string
  odds: string
  is_winner: boolean | null
  market_id?: number
  market_type?: string
}

export interface Market {
  id: number
  type: string
  name: string
  is_live: boolean
  selections: Selection[]
}

export interface EventItem {
  id: number
  sport: number
  sport_name: string
  team_home: string
  team_away: string
  start_time: string
  status: string
  market_count: number
  main_odds?: { id: number; name: string; odds: string }[]
}

export interface EventDetail {
  id: number
  sport: Sport
  team_home: string
  team_away: string
  start_time: string
  status: string
  created_at: string
  market_count: number
  markets: Market[]
}

export const events = {
  list: async (params?: { sport?: string; status?: string }): Promise<EventItem[]> => {
    const response = await api.get('/events/', { params })
    return response.data.results || response.data
  },

  detail: async (id: number): Promise<EventDetail> => {
    const response = await api.get(`/events/${id}/`)
    return response.data
  },

  live: async (): Promise<EventItem[]> => {
    const response = await api.get('/events/live/')
    return response.data.results || response.data
  },

  sports: async (): Promise<Sport[]> => {
    const response = await api.get('/events/sports/')
    return response.data.results || response.data
  },
}
