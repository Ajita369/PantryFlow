import type { MealSuggestion } from './mealsApi'
import type { ShoppingListItem, ShoppingTotals } from './planningApi'

export type AiResponse = {
  message: string
  source: string
  fallback: boolean
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function getMealExplanation(meal: MealSuggestion) {
  const response = await fetch('/api/ai/meal-explanation/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: meal.title,
      description: meal.description,
      matched_ingredients: meal.matched_ingredients,
      missing_ingredients: meal.missing_ingredients,
      substitutions: meal.substitutions,
    }),
  })
  return handleResponse<AiResponse>(response)
}

export async function getSubstitutionHelp(meal: MealSuggestion) {
  const response = await fetch('/api/ai/substitution/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      missing_ingredients: meal.missing_ingredients,
      substitutions: meal.substitutions,
    }),
  })
  return handleResponse<AiResponse>(response)
}

export async function getShoppingNotes(
  items: ShoppingListItem[],
  totals: ShoppingTotals | null
) {
  const response = await fetch('/api/ai/shopping-notes/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items,
      totals,
    }),
  })
  return handleResponse<AiResponse>(response)
}
