export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export const TENANTS = [
  'studio.zerostic.com',
  'pm.zerostic.com',
  'dev.zerostic.com',
] as const

export type Tenant = typeof TENANTS[number]
