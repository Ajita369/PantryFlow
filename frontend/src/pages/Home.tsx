import { useEffect, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, type DashboardResponse } from '../api/dashboardApi'
import EmptyState from '../components/EmptyState'
import heroImage from '../assets/hero.png'

function formatCurrency(amount: string | number | null | undefined, currency: string) {
  if (amount === null || amount === undefined || amount === '') {
    return '—'
  }
  const value = typeof amount === 'string' ? Number(amount) : amount
  if (Number.isNaN(value)) {
    return '—'
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value)
}

function Home() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const heroStyle = {
    '--hero-image': `url(${heroImage})`,
  } as CSSProperties

  useEffect(() => {
    let isMounted = true

    getDashboard()
      .then((data) => {
        if (isMounted) {
          setDashboard(data)
        }
      })
      .catch((err: Error) => {
        if (isMounted) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <section className="page home-page">
      <div className="page-header hero hero-banner" style={heroStyle}>
        <div className="hero-content">
          <p className="eyebrow">Dashboard</p>
          <h1 className="hero-title">Plan smarter with what you already own.</h1>
          <p className="hero-subtitle">
            PantryFlow highlights urgent items, quick wins, and budget signals so
            you can cook with confidence.
          </p>
          <div className="hero-meta">
            <span>Fresh insights · Zero waste focus</span>
            <span>Updated weekly</span>
          </div>
        </div>
      </div>

      {error ? <p className="status status-error">{error}</p> : null}

      {loading ? (
        <div className="grid dashboard-grid">
          <div className="card skeleton-card">
            <div className="skeleton-line" />
            <div className="skeleton-line wide" />
          </div>
          <div className="card skeleton-card">
            <div className="skeleton-line" />
            <div className="skeleton-line wide" />
          </div>
          <div className="card skeleton-card">
            <div className="skeleton-line" />
            <div className="skeleton-line wide" />
          </div>
          <div className="card skeleton-card">
            <div className="skeleton-line" />
            <div className="skeleton-line wide" />
          </div>
          <div className="card skeleton-card">
            <div className="skeleton-line" />
            <div className="skeleton-line wide" />
          </div>
        </div>
      ) : dashboard ? (
        <>
          <div className="grid dashboard-grid">
            <article className="card stat-card">
              <p className="stat-label">Pantry items</p>
              <p className="stat-value">{dashboard.pantry_count}</p>
              <p className="muted">Items tracked right now.</p>
            </article>
            <article className="card stat-card">
              <p className="stat-label">Expiring soon</p>
              <p className="stat-value">{dashboard.expiring_soon_count}</p>
              <p className="muted">Next 7 days.</p>
            </article>
            <article className="card stat-card">
              <p className="stat-label">Meals ready</p>
              <p className="stat-value">{dashboard.quick_meals.length}</p>
              <p className="muted">Cook-today ideas.</p>
            </article>
            <article className="card stat-card">
              <p className="stat-label">Budget remaining</p>
              <p className="stat-value">
                {formatCurrency(dashboard.budget_remaining, dashboard.currency)}
              </p>
              <p className="muted">
                Budget total:{' '}
                {formatCurrency(dashboard.budget_total, dashboard.currency)}
              </p>
            </article>
            <article className="card stat-card">
              <p className="stat-label">Shopping list</p>
              <p className="stat-value">{dashboard.shopping_count}</p>
              <p className="muted">Items still needed.</p>
            </article>
          </div>

          <div className="grid dashboard-split">
            <article className="card">
              <h2>Urgent items</h2>
              {dashboard.top_urgent_items.length ? (
                <div className="urgent-grid">
                  {dashboard.top_urgent_items.map((item) => (
                    <div key={item.id} className="urgent-chip">
                      <div>
                        <strong>{item.name}</strong>
                        <span className="muted">{item.category || 'Uncategorized'}</span>
                      </div>
                      <span
                        className={`badge badge-${item.urgency_label
                          .toLowerCase()
                          .replace(' ', '-')}`}
                      >
                        {item.urgency_label}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No urgent items"
                  message="Your pantry looks stable. Add more items to see urgency alerts."
                  action={
                    <Link to="/pantry" className="button ghost">
                      Add pantry items
                    </Link>
                  }
                />
              )}
            </article>
            <article className="card">
              <h2>Quick meals</h2>
              {dashboard.quick_meals.length ? (
                <ul className="quick-list">
                  {dashboard.quick_meals.map((meal) => (
                    <li key={meal.id}>
                      <strong>{meal.title}</strong>
                      <span>
                        Match {Math.round(meal.match_score * 100)}% ·{' '}
                        {meal.estimated_time_minutes} min
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  title="No quick meals yet"
                  message="Generate meals to populate quick-cook ideas."
                  action={
                    <Link to="/meals" className="button ghost">
                      Generate meals
                    </Link>
                  }
                />
              )}
            </article>
          </div>
        </>
      ) : null}
    </section>
  )
}

export default Home
