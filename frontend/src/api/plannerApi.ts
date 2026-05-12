import type { AiResponse } from './aiApi'
import { authFetch } from './authApi'
import type { MealSuggestion, UrgentItem } from './mealsApi'
import type { ShoppingTotals, WeeklyBudget } from './planningApi'

export type ShoppingPlanItem = {
  name: string
  estimated_price: string
  quantity: string
  unit: string
  priority: number
  reason: string
}

export type PlanResponse = {
  generated_at: string
  tasks: string[]
  warnings: string[]
  budget: WeeklyBudget | null
  urgent_items: UrgentItem[]
  meals: {
    cook_today: MealSuggestion[]
    cook_this_week: MealSuggestion[]
    possible_later: MealSuggestion[]
  }
  substitutions: Array<{ ingredient: string; options: string[] }>
  shopping: {
    items: ShoppingPlanItem[]
    totals: ShoppingTotals
  }
  explanation: AiResponse
}

export type SavedPlanResponse = {
  plan: PlanResponse | null
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function getSavedWeeklyPlan() {
  const response = await authFetch('/api/plan-week/')
  return handleResponse<SavedPlanResponse>(response)
}

export async function generateWeeklyPlan() {
  const response = await authFetch('/api/plan-week/', {
    method: 'POST',
  })
  const data = await handleResponse<SavedPlanResponse>(response)
  if (!data.plan) {
    throw new Error('Planner did not return a generated plan.')
  }
  return data.plan
}
