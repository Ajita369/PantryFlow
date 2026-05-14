import { authFetch } from './authApi'

export type DashboardUrgentItem = {
  id: number
  name: string
  category: string
  quantity: string
  unit: string
  expiry_date: string | null
  urgency_score: number
  urgency_label: string
}

export type DashboardQuickMeal = {
  id: number
  title: string
  match_score: number
  estimated_time_minutes: number
}

export type DashboardResponse = {
  pantry_count: number
  expiring_soon_count: number
  expired_count: number
  budget_remaining: string | null
  budget_total: string | null
  currency: string
  top_urgent_items: DashboardUrgentItem[]
  quick_meals: DashboardQuickMeal[]
  shopping_count: number
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function getDashboard() {
  const response = await authFetch('/api/dashboard/')
  return handleResponse<DashboardResponse>(response)
}
