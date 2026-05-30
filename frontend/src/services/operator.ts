import api from './api'

export interface OperatorMetrics {
  total_stakes: string
  total_payouts: string
  ggr: string
  total_bets: number
  active_users: number
  active_bets: number
}

export interface ExposureItem {
  selection_id: number
  selection_name: string
  odds: string
  bets_count: number
  potential_payout: string
}

export interface ExposureSummaryItem {
  event_id: number
  team_home: string
  team_away: string
  sport: string
  start_time: string
  status: string
  total_bets: number
  max_payout: string
}

export const operator = {
  getMetrics: async (): Promise<OperatorMetrics> => {
    const response = await api.get('/operator/metrics/')
    return response.data
  },

  getExposure: async (eventId: number): Promise<ExposureItem[]> => {
    const response = await api.get(`/operator/exposure/${eventId}/`)
    return response.data
  },

  getExposureSummary: async (): Promise<ExposureSummaryItem[]> => {
    const response = await api.get('/operator/exposure/')
    return response.data
  },

  getReportURL: (mes: number, anio: number): string => {
    const params = new URLSearchParams({ mes: String(mes), anio: String(anio) })
    return `/api/operator/reporte/?${params.toString()}`
  },

  downloadReport: async (mes: number, anio: number): Promise<Blob> => {
    const response = await api.get('/operator/reporte/', {
      params: { mes, anio },
      responseType: 'blob',
    })
    return response.data
  },
}
