export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export const TENANTS = [
  'zerostic.com',
] as const

export type Tenant = typeof TENANTS[number]
