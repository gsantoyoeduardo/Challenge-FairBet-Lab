import api from './api'

export interface AdminBet {
  id: number
  username: string
  stake: string
  total_odds: string
  status: string
  placed_at: string
  settled_at: string | null
  payout: string | null
  selections: {
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
  }[]
}

export interface SelectionWinner {
  selection_id: number
  selection_name: string
  market: string
  event: string
  is_winner: boolean
}

export const adminBetting = {
  getActiveBets: async (): Promise<AdminBet[]> => {
    const response = await api.get('/operator/bets/', {
      params: { status: 'accepted' },
    })
    return response.data.results || response.data
  },

  getAllBets: async (): Promise<AdminBet[]> => {
    const response = await api.get('/operator/bets/')
    return response.data.results || response.data
  },

  liquidateBet: async (betId: number, winningSelectionIds?: number[]): Promise<AdminBet> => {
    const response = await api.post(`/betting/liquidar/${betId}/`, {
      winning_selection_ids: winningSelectionIds,
    })
    return response.data
  },

  setSelectionWinner: async (selectionId: number, isWinner: boolean): Promise<SelectionWinner> => {
    const response = await api.post(`/events/selections/${selectionId}/winner/`, {
      is_winner: isWinner,
    })
    return response.data
  },
}
