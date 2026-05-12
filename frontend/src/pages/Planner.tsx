import { useEffect, useState } from 'react'
import {
  generateWeeklyPlan,
  getSavedWeeklyPlan,
  type PlanResponse,
  type ShoppingPlanItem,
} from '../api/plannerApi'
import type { MealSuggestion, UrgentItem } from '../api/mealsApi'

const priorityLabel: Record<number, string> = {
  1: 'High',
  2: 'Medium',
  3: 'Low',
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

function UrgentItemChip({ item }: { item: UrgentItem }) {
  return (
    <div className="urgent-chip">
      <div>
        <strong>{item.name}</strong>
        <span className="muted">{item.category || 'Uncategorized'}</span>
      </div>
      <span className={`badge badge-${item.urgency_label.toLowerCase().replace(' ', '-')}`}>
        {item.urgency_label}
      </span>
    </div>
  )
}

function MealGroup({ title, meals }: { title: string; meals: MealSuggestion[] }) {
  return (
    <div className="planner-block">
      <h4>{title}</h4>
      {meals.length ? (
        <ul className="planner-list">
          {meals.map((meal) => (
            <li key={meal.id} className="planner-meal">
              <strong>{meal.title}</strong>
              <span>
                Match {Math.round(meal.match_score * 100)}% · {meal.matched_ingredients.length}
                {' matched, '}
                {meal.missing_ingredients.length} missing
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">No meals in this group yet.</p>
      )}
    </div>
  )
}

function ShoppingTable({ items, currency }: { items: ShoppingPlanItem[]; currency: string }) {
  if (!items.length) {
    return <p className="muted">No shopping items suggested.</p>
  }

  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            <th>Item</th>
            <th>Qty</th>
            <th>Priority</th>
            <th>Estimated</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => {
            const label = priorityLabel[item.priority] ?? 'Medium'
            return (
              <tr key={`${item.name}-${index}`}>
                <td>
                  <div className="item-name">
                    {item.name}
                    {item.reason ? <span className="item-reason">{item.reason}</span> : null}
                  </div>
                </td>
                <td>
                  {item.quantity} {item.unit}
                </td>
                <td>
                  <span className={`badge badge-${label.toLowerCase()}`}>{label}</span>
                </td>
                <td>{formatCurrency(item.estimated_price, currency)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function Planner() {
  const [plan, setPlan] = useState<PlanResponse | null>(null)
  const [loadingSaved, setLoadingSaved] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    async function loadSavedPlan() {
      setLoadingSaved(true)
      setError(null)
      try {
        const response = await getSavedWeeklyPlan()
        if (!ignore) {
          setPlan(response.plan)
        }
      } catch (err) {
        if (!ignore) {
          const message = err instanceof Error ? err.message : 'Failed to load saved plan.'
          setError(message)
        }
      } finally {
        if (!ignore) {
          setLoadingSaved(false)
        }
      }
    }

    loadSavedPlan()

    return () => {
      ignore = true
    }
  }, [])

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await generateWeeklyPlan()
      setPlan(response)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to build plan.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const currency = plan?.shopping?.totals?.currency || 'USD'

  return (
    <section className="page">
      <div className="page-header">
        <h1>Planner</h1>
        <p>LangGraph turns pantry, meals, and budget signals into a weekly plan.</p>
      </div>

      <section className="card">
        <div className="toolbar">
          <div>
            <h2>Weekly plan</h2>
            <p className="muted">AI writes the summary. The plan logic stays rule-based.</p>
          </div>
          <div className="toolbar-group">
            <button type="button" className="button" onClick={handleGenerate} disabled={loading}>
              {loading ? 'Planning...' : 'Generate plan'}
            </button>
          </div>
        </div>

        {error ? <p className="status status-error">{error}</p> : null}
        {loadingSaved ? <p className="status status-wait">Loading saved plan...</p> : null}
        {loading ? <p className="status status-wait">Building your plan...</p> : null}

        {!loadingSaved && plan ? (
          <>
            <div className="summary-row">
              <div className="summary-card">
                <span>Tasks</span>
                <div className="tag-list">
                  {plan.tasks.length ? (
                    plan.tasks.map((task) => (
                      <span key={task} className="tag tag-ok">
                        {task}
                      </span>
                    ))
                  ) : (
                    <span className="tag">No tasks queued</span>
                  )}
                </div>
              </div>
              <div className="summary-card">
                <span>Urgent items</span>
                <strong>{plan.urgent_items.length}</strong>
              </div>
              <div className="summary-card">
                <span>Shopping suggestions</span>
                <strong>{plan.shopping.items.length}</strong>
              </div>
            </div>

            {plan.warnings.length ? (
              <div className="planner-warning">
                {plan.warnings.map((warning, index) => (
                  <p key={index}>{warning}</p>
                ))}
              </div>
            ) : null}

            {plan.explanation?.message ? (
              <div className="ai-panel">
                <p>{plan.explanation.message}</p>
                <span className="ai-meta">
                  Source: {plan.explanation.source}
                  {plan.explanation.fallback ? ' (fallback)' : ''}
                </span>
              </div>
            ) : null}

            <div className="planner-grid">
              <article className="planner-card">
                <h3>Urgency focus</h3>
                {plan.urgent_items.length ? (
                  <div className="urgent-grid">
                    {plan.urgent_items.map((item) => (
                      <UrgentItemChip key={item.id} item={item} />
                    ))}
                  </div>
                ) : (
                  <p className="muted">No urgent items right now.</p>
                )}
              </article>

              <article className="planner-card">
                <h3>Meals</h3>
                <MealGroup title="Cook today" meals={plan.meals.cook_today} />
                <MealGroup title="Cook this week" meals={plan.meals.cook_this_week} />
                <MealGroup title="Possible later" meals={plan.meals.possible_later} />
              </article>

              <article className="planner-card">
                <h3>Shopping</h3>
                <ShoppingTable items={plan.shopping.items} currency={currency} />
              </article>

              <article className="planner-card">
                <h3>Substitutions</h3>
                {plan.substitutions.length ? (
                  <ul className="planner-list">
                    {plan.substitutions.map((entry) => (
                      <li key={entry.ingredient}>
                        <strong>{entry.ingredient}:</strong>{' '}
                        {entry.options.length ? entry.options.join(', ') : 'No swaps yet'}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No substitutions needed.</p>
                )}
              </article>

              <article className="planner-card">
                <h3>Budget impact</h3>
                <div className="summary-row">
                  <div className="summary-card">
                    <span>Total estimated</span>
                    <strong>
                      {formatCurrency(plan.shopping.totals.total_estimated_cost, currency)}
                    </strong>
                  </div>
                  <div className="summary-card">
                    <span>Budget remaining</span>
                    <strong>
                      {formatCurrency(plan.shopping.totals.budget_remaining, currency)}
                    </strong>
                  </div>
                </div>
                {plan.budget ? (
                  <p className="muted">
                    Budget window {plan.budget.week_start_date} - {plan.budget.week_end_date}
                  </p>
                ) : (
                  <p className="muted">No weekly budget saved yet.</p>
                )}
              </article>
            </div>
          </>
        ) : !loadingSaved ? (
          <p className="empty">Generate a plan to see your weekly lineup.</p>
        ) : null}
      </section>
    </section>
  )
}

export default Planner
