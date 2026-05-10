import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Register() {
  const { register, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (!email.trim()) {
      setError('Email is required.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await register({
        email: email.trim(),
        first_name: firstName.trim(),
        display_name: displayName.trim(),
        password,
        password_confirm: confirm,
      })
      navigate('/', { replace: true })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page auth-page">
      <div className="page-header">
        <h1>Create account</h1>
        <p>Set up your PantryFlow profile to keep data private.</p>
      </div>

      <section className="card auth-card">
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-grid">
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
              <span>First name</span>
              <input
                name="first_name"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                placeholder="Alex"
              />
            </label>
            <label className="field">
              <span>Display name</span>
              <input
                name="display_name"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="Alex P."
              />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                name="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 8 characters"
                required
              />
            </label>
            <label className="field">
              <span>Confirm password</span>
              <input
                type="password"
                name="password_confirm"
                value={confirm}
                onChange={(event) => setConfirm(event.target.value)}
                placeholder="Re-enter your password"
                required
              />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="button" disabled={loading}>
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </div>
          {error ? <p className="status status-error">{error}</p> : null}
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>.
        </p>
      </section>
    </section>
  )
}

export default Register
