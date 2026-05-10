import { authFetch } from './authApi'

export type WeeklyBudget = {
  id: number
  weekly_budget_amount: string
  currency: string
  week_start_date: string
  week_end_date: string
  created_at: string
  updated_at: string
}

export type BudgetResponse = {
  budget: WeeklyBudget | null
}

export type BudgetInput = {
  weekly_budget_amount: number
  currency: string
}

export type ShoppingListItem = {
  id: number
  name: string
  estimated_price: string
  quantity: string
  unit: string
  priority: number
  is_needed: boolean
  reason: string
  linked_pantry_item: number | null
  created_at: string
  updated_at: string
}

export type ShoppingTotals = {
  total_estimated_cost: string
  budget_amount: string | null
  budget_remaining: string | null
  currency: string
}

export type ShoppingListResponse = {
  items: ShoppingListItem[]
  totals: ShoppingTotals
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function getBudget() {
  const response = await authFetch('/api/budget/')
  return handleResponse<BudgetResponse>(response)
}

export async function saveBudget(payload: BudgetInput) {
  const response = await authFetch('/api/budget/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<BudgetResponse>(response)
}

export async function getShoppingList() {
  const response = await authFetch('/api/shopping-list/')
  return handleResponse<ShoppingListResponse>(response)
}

export async function generateShoppingList() {
  const response = await authFetch('/api/shopping-list/generate/', {
    method: 'POST',
  })
  return handleResponse<ShoppingListResponse>(response)
}

export async function updateShoppingItem(
  id: number,
  payload: Partial<Pick<ShoppingListItem, 'is_needed' | 'priority'>>
) {
  const response = await authFetch(`/api/shopping-list/${id}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<ShoppingListItem>(response)
}
