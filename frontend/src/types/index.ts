export interface User {
  id: number
  username: string
  email: string
  dni: string
  estado_cuenta: string
  date_joined: string
  is_staff: boolean
}

export interface AuthTokens {
  access: string
  refresh: string
  user: User
}

export interface WalletBalance {
  balance: string
}

export interface TransactionRequest {
  amount: string
  reference?: string
  idempotency_key?: string
}
