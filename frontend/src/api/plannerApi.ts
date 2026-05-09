import type { AiResponse } from './aiApi'
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

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function getWeeklyPlan() {
  const response = await fetch('/api/plan-week/')
  return handleResponse<PlanResponse>(response)
}
