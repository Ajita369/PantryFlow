import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import {
  getBudget,
  getShoppingList,
  saveBudget,
  type ShoppingTotals,
  type WeeklyBudget,
} from '../api/planningApi'
import EmptyState from '../components/EmptyState'
import Toast from '../components/Toast'
import { useToast } from '../hooks/useToast'

type BudgetFormState = {
  weekly_budget_amount: string
  currency: string
}

const initialForm: BudgetFormState = {
  weekly_budget_amount: '',
  currency: 'USD',
}

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

function Budget() {
  const [budget, setBudget] = useState<WeeklyBudget | null>(null)
  const [totals, setTotals] = useState<ShoppingTotals | null>(null)
  const [formState, setFormState] = useState<BudgetFormState>(initialForm)
  const [loading, setLoading] = useState(false)
  const [loadingView, setLoadingView] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const { toast, showToast, clearToast } = useToast()

  const loadBudget = async () => {
    try {
      const response = await getBudget()
      setBudget(response.budget)
      if (response.budget) {
        setFormState({
          weekly_budget_amount: response.budget.weekly_budget_amount,
          currency: response.budget.currency,
        })
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load budget.'
      setError(message)
    }
  }

  const loadTotals = async () => {
    try {
      const response = await getShoppingList()
      setTotals(response.totals)
    } catch {
      setTotals(null)
    }
  }

  useEffect(() => {
    let isMounted = true

    async function loadAll() {
      setLoadingView(true)
      await Promise.all([loadBudget(), loadTotals()])
      if (isMounted) {
        setLoadingView(false)
      }
    }

    loadAll()

    return () => {
      isMounted = false
    }
  }, [])

  const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setNotice(null)

    const amount = Number(formState.weekly_budget_amount)
    if (!amount || amount < 0) {
      setError('Enter a valid weekly budget amount.')
      return
    }

    setLoading(true)
    try {
      const response = await saveBudget({
        weekly_budget_amount: amount,
        currency: formState.currency,
      })
      setBudget(response.budget)
      setNotice('Budget updated.')
      showToast('Budget saved.', 'success')
      await loadTotals()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save budget.'
      setError(message)
      showToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const currency = budget?.currency || totals?.currency || formState.currency

  return (
    <section className="page">
      <div className="page-header">
        <h1>Budget</h1>
        <p>Set a weekly budget and keep grocery spending on track.</p>
      </div>

      <div className="grid stats-grid">
        {loadingView ? (
          <>
            <article className="card skeleton-card" />
            <article className="card skeleton-card" />
            <article className="card skeleton-card" />
          </>
        ) : (
          <>
            <article className="card">
              <h2>Weekly budget</h2>
              {budget ? (
                <>
                  <p className="stat-value">
                    {formatCurrency(budget.weekly_budget_amount, currency)}
                  </p>
                  <p className="muted">
                    {budget.week_start_date} to {budget.week_end_date}
                  </p>
                </>
              ) : (
                <EmptyState
                  title="No budget yet"
                  message="Set a weekly target to track spending."
                />
              )}
            </article>
            <article className="card">
              <h2>Estimated spend</h2>
              <p className="stat-value">
                {formatCurrency(totals?.total_estimated_cost, currency)}
              </p>
              <p className="muted">From the current shopping list.</p>
            </article>
            <article className="card">
              <h2>Budget remaining</h2>
              <p className="stat-value">
                {formatCurrency(totals?.budget_remaining, currency)}
              </p>
              <p className="muted">Update the list to refresh this number.</p>
            </article>
          </>
        )}
      </div>

      <section className="card">
        <h2>Set weekly budget</h2>
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="field">
              <span>Budget amount</span>
              <input
                name="weekly_budget_amount"
                value={formState.weekly_budget_amount}
                onChange={handleChange}
                placeholder="120"
                type="number"
                min="0"
                step="0.01"
                required
              />
            </label>
            <label className="field">
              <span>Currency</span>
              <select name="currency" value={formState.currency} onChange={handleChange}>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="button" disabled={loading}>
              {loading ? 'Saving...' : 'Save budget'}
            </button>
          </div>
          {notice ? <p className="status status-ok">{notice}</p> : null}
          {error ? <p className="status status-error">{error}</p> : null}
        </form>
      </section>
      <Toast toast={toast} onClose={clearToast} />
    </section>
  )
}

export default Budget
