import api from './api'

export interface BetSelectionDetail {
  selection_id: number
  selection_name: string
  market_type: string
  market_name: string
  event: {
    id: number
    home: string
    away: string
  }
  odds_at_time: string
}

export interface Bet {
  id: number
  username: string
  stake: string
  total_odds: string
  status: string
  placed_at: string
  settled_at: string | null
  payout: string | null
  selections: BetSelectionDetail[]
  cashout_preview: string | null
}

export interface ApostarRequest {
  selections: { selection_id: number }[]
  stake: string
  expected_odds?: Record<string, string>
  sistema_tipo?: string
  idempotency_key?: string
}

export interface CashOutRequest {
  idempotency_key?: string
}

export interface CashOutPreview {
  bet_id: number
  stake: string
  total_odds: string
  cashout_amount: string
}

export const betting = {
  apostar: async (data: ApostarRequest): Promise<Bet> => {
    const response = await api.post('/betting/apuesta/', data)
    return response.data
  },

  cashOut: async (betId: number, data: CashOutRequest): Promise<Bet> => {
    const response = await api.post(`/betting/cash-out/${betId}/`, data)
    return response.data
  },

  cashOutPreview: async (betId: number): Promise<CashOutPreview> => {
    const response = await api.get(`/betting/cash-out/${betId}/preview/`)
    return response.data
  },

  misApuestas: async (params?: { status?: string }): Promise<Bet[]> => {
    const response = await api.get('/betting/mis-apuestas/', { params })
    return response.data.results || response.data
  },
}
