import { authFetch } from './authApi'

export type UrgentItem = {
  id: number
  name: string
  category: string
  quantity: string
  unit: string
  expiry_date: string | null
  urgency_score: number
  urgency_label: string
}

export type MealSuggestion = {
  id: number
  title: string
  description: string
  cuisine_type: string
  estimated_cost: number
  estimated_time_minutes: number
  steps: string[]
  matched_ingredients: string[]
  missing_ingredients: string[]
  substitutions: Record<string, string[]>
  match_score: number
  source: string
}

export type MealSuggestionsResponse = {
  urgent_items: UrgentItem[]
  meals: {
    cook_today: MealSuggestion[]
    cook_this_week: MealSuggestion[]
    possible_later: MealSuggestion[]
  }
  source: string
  llm_error?: string | null
  generated_at: string
  cached: boolean
  pantry_changed?: boolean
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function getMealSuggestions() {
  const response = await authFetch('/api/meals/suggestions/')
  return handleResponse<MealSuggestionsResponse>(response)
}

export async function generateMeals() {
  const response = await authFetch('/api/meals/generate/', {
    method: 'POST',
  })
  return handleResponse<MealSuggestionsResponse>(response)
}
