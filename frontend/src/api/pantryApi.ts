import { authFetch, getApiBase } from './authApi'

export type PantryItem = {
  id: number
  name: string
  category: string
  quantity: string
  unit: string
  expiry_date: string | null
  purchase_date: string | null
  notes: string
  location: string
  created_at: string
  updated_at: string
}

export type PantryItemInput = {
  name: string
  category: string
  quantity: number
  unit: string
  expiry_date: string | null
  purchase_date: string | null
  notes: string
  location: string
}

type PantryListFilters = {
  search?: string
  category?: string
}

const baseUrl = `${getApiBase()}/api/pantry-items/`

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

export async function listPantryItems(filters: PantryListFilters = {}) {
  const params = new URLSearchParams()
  if (filters.search) {
    params.set('search', filters.search)
  }
  if (filters.category) {
    params.set('category', filters.category)
  }

  const url = params.toString() ? `${baseUrl}?${params}` : baseUrl
  const response = await authFetch(url)
  return handleResponse<PantryItem[]>(response)
}

export async function createPantryItem(payload: PantryItemInput) {
  const response = await authFetch(baseUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<PantryItem>(response)
}

export async function updatePantryItem(id: number, payload: PantryItemInput) {
  const response = await authFetch(`${baseUrl}${id}/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse<PantryItem>(response)
}

export async function deletePantryItem(id: number) {
  const response = await authFetch(`${baseUrl}${id}/`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Delete failed')
  }
}
