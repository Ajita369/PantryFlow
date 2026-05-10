import {
  clearTokens,
  getAccessToken,
  getMe,
  login,
  logout,
  register,
  type AuthUser,
  type LoginPayload,
  type RegisterPayload,
} from '../api/authApi'
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

type AuthContextValue = {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const bootstrap = async () => {
      if (!getAccessToken()) {
        setIsLoading(false)
        return
      }

      try {
        const profile = await getMe()
        setUser(profile)
      } catch {
        clearTokens()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    bootstrap()
  }, [])

  const handleLogin = async (payload: LoginPayload) => {
    const result = await login(payload)
    setUser(result.user)
  }

  const handleRegister = async (payload: RegisterPayload) => {
    const result = await register(payload)
    setUser(result.user)
  }

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      clearTokens()
      setUser(null)
    }
  }

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login: handleLogin,
      register: handleRegister,
      logout: handleLogout,
    }),
    [user, isLoading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export function RequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <section className="page">
        <p className="status status-wait">Checking session...</p>
      </section>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}
