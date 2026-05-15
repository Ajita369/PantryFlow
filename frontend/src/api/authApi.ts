// In production the frontend (Vercel) and backend (Render) are on different origins.
// Set VITE_API_BASE_URL in Vercel's environment variables to your Render backend URL, e.g.:
//   https://pantryflow-api.onrender.com
// In development leave it unset - the Vite proxy forwards /api/* to localhost:8000.
export function getApiBase(): string {
  return (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
}

export type AuthTokens = {
  access: string
  refresh: string
}

export type AuthUser = {
  id: number
  email: string
  first_name: string
  display_name: string
}

export type RegisterPayload = {
  email: string
  password: string
  password_confirm: string
  first_name?: string
  display_name?: string
}

export type LoginPayload = {
  email: string
  password: string
}

type RegisterResponse = {
  user: AuthUser
  tokens: AuthTokens
}

type LoginResponse = {
  access: string
  refresh: string
  user: AuthUser
}

const ACCESS_TOKEN_KEY = 'pf_access_token'
const REFRESH_TOKEN_KEY = 'pf_refresh_token'
const AUTH_EXPIRED_EVENT = 'pf-auth-expired'
const TOKEN_REFRESH_WINDOW_SECONDS = 30

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(tokens: AuthTokens) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function notifyAuthExpired() {
  window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
}

export function onAuthExpired(callback: () => void) {
  window.addEventListener(AUTH_EXPIRED_EVENT, callback)
  return () => window.removeEventListener(AUTH_EXPIRED_EVENT, callback)
}

function getTokenExpiry(token: string | null) {
  if (!token) {
    return null
  }

  try {
    const [, payload] = token.split('.')
    if (!payload) {
      return null
    }
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = JSON.parse(atob(normalized)) as { exp?: number }
    return decoded.exp ?? null
  } catch {
    return null
  }
}

function isTokenExpiring(token: string | null) {
  const expiry = getTokenExpiry(token)
  if (!expiry) {
    return false
  }
  return expiry <= Math.floor(Date.now() / 1000) + TOKEN_REFRESH_WINDOW_SECONDS
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Request failed')
  }
  return response.json() as Promise<T>
}

async function refreshAccessToken() {
  const refresh = getRefreshToken()
  if (!refresh) {
    return null
  }

  const response = await fetch(`${getApiBase()}/api/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })

  if (!response.ok) {
    clearTokens()
    notifyAuthExpired()
    return null
  }

  const data = (await response.json()) as { access: string }
  setTokens({ access: data.access, refresh })
  return data.access
}

function withAuthHeaders(init: RequestInit, accessToken: string | null) {
  const headers = new Headers(init.headers || {})
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }
  return { ...init, headers }
}

export async function authFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  let accessToken = getAccessToken()
  if (isTokenExpiring(accessToken)) {
    accessToken = await refreshAccessToken()
  }

  const response = await fetch(input, withAuthHeaders(init, accessToken))
  if (response.status !== 401) {
    return response
  }

  const existingHeaders = new Headers(init.headers || {})
  if (existingHeaders.get('x-auth-retry') === 'true') {
    return response
  }

  const refreshed = await refreshAccessToken()
  if (!refreshed) {
    notifyAuthExpired()
    return response
  }

  const retryHeaders = new Headers(init.headers || {})
  retryHeaders.set('x-auth-retry', 'true')
  retryHeaders.set('Authorization', `Bearer ${refreshed}`)

  return fetch(input, { ...init, headers: retryHeaders })
}

export async function register(payload: RegisterPayload) {
  const response = await fetch(`${getApiBase()}/api/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await handleResponse<RegisterResponse>(response)
  setTokens(data.tokens)
  return data
}

export async function login(payload: LoginPayload) {
  const response = await fetch(`${getApiBase()}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await handleResponse<LoginResponse>(response)
  const tokens = { access: data.access, refresh: data.refresh }
  setTokens(tokens)
  return { user: data.user, tokens }
}

export async function logout() {
  const refresh = getRefreshToken()
  if (!refresh) {
    clearTokens()
    return
  }

  const response = await authFetch(`${getApiBase()}/api/auth/logout/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })

  if (!response.ok) {
    clearTokens()
    const errorText = await response.text()
    throw new Error(errorText || 'Logout failed')
  }

  clearTokens()
}

export async function getMe() {
  const response = await authFetch(`${getApiBase()}/api/auth/me/`)
  return handleResponse<AuthUser>(response)
}
