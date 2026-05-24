export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export interface Thread {
  id: string
  title: string
  createdAt: number
  updatedAt: number
}

export const TENANTS = [
  'zerostic.com',
] as const

export type Tenant = typeof TENANTS[number]
