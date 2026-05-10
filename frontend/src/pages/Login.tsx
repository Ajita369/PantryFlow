import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { from?: Location } | null
  const redirectTo = state?.from?.pathname || '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (!email.trim() || !password.trim()) {
      setError('Email and password are required.')
      return
    }

    setLoading(true)
    try {
      await login({ email: email.trim(), password })
      navigate(redirectTo, { replace: true })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page auth-page">
      <div className="page-header">
        <h1>Sign in</h1>
        <p>Welcome back. Enter your details to continue.</p>
      </div>

      <section className="card auth-card">
        <form className="form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              name="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              name="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              required
            />
          </label>
          <div className="form-actions">
            <button type="submit" className="button" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
          {error ? <p className="status status-error">{error}</p> : null}
        </form>

        <p className="auth-footer">
          New here? <Link to="/register">Create an account</Link>.
        </p>
      </section>
    </section>
  )
}

export default Login
