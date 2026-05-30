import api from './api'

export interface AdminEvent {
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

export interface AdminEventDetail {
  id: number
  sport: { id: number; name: string; slug: string }
  team_home: string
  team_away: string
  start_time: string
  status: string
  markets: {
    id: number
    type: string
    name: string
    is_live: boolean
    suspended_until: string | null
    selections: {
      id: number
      name: string
      odds: string
      is_winner: boolean | null
      market_id: number
      market_type: string
    }[]
  }[]
}

export interface CreateEventRequest {
  sport_slug: string
  team_home: string
  team_away: string
  start_time: string
  status?: string
}

export const adminEvents = {
  list: async (params?: { sport?: string; status?: string }): Promise<AdminEvent[]> => {
    const response = await api.get('/events/', { params })
    return response.data.results || response.data
  },

  detail: async (id: number): Promise<AdminEventDetail> => {
    const response = await api.get(`/events/${id}/`)
    return response.data
  },

  create: async (data: CreateEventRequest): Promise<AdminEvent> => {
    const response = await api.post('/events/create/', data)
    return response.data
  },

  changeStatus: async (eventId: number, status: string): Promise<any> => {
    const response = await api.post(`/events/${eventId}/status/`, { status })
    return response.data
  },

  setSelectionWinner: async (selectionId: number, isWinner: boolean): Promise<any> => {
    const response = await api.post(`/events/selections/${selectionId}/winner/`, { is_winner: isWinner })
    return response.data
  },

  suspendMarket: async (marketId: number, seconds?: number): Promise<any> => {
    const response = await api.post(`/events/markets/${marketId}/suspend/`, {
      suspended_until: seconds ?? null,
    })
    return response.data
  },

  sports: async (): Promise<{ id: number; name: string; slug: string }[]> => {
    const response = await api.get('/events/sports/')
    return response.data.results || response.data
  },

  getExposure: async (eventId: number): Promise<{
    selection_id: number
    selection_name: string
    odds: string
    bets_count: number
    potential_payout: string
  }[]> => {
    const response = await api.get(`/operator/exposure/${eventId}/`)
    return response.data
  },
}
