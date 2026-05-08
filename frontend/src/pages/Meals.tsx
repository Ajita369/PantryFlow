import { useEffect, useState } from 'react'
import {
  getMealSuggestions,
  type MealSuggestion,
  type MealSuggestionsResponse,
  type UrgentItem,
} from '../api/mealsApi'

function MealCard({ meal }: { meal: MealSuggestion }) {
  return (
    <article className="meal-card">
      <div className="meal-header">
        <div>
          <h3>{meal.title}</h3>
          <p className="muted">{meal.description}</p>
        </div>
        <span className="meal-score">Match {Math.round(meal.match_score * 100)}%</span>
      </div>
      <div className="meal-meta">
        <span>{meal.cuisine_type}</span>
        <span>{meal.estimated_time_minutes} min</span>
        <span>${meal.estimated_cost.toFixed(2)}</span>
      </div>
      <div className="meal-section">
        <p className="section-label">Matched ingredients</p>
        <div className="tag-list">
          {meal.matched_ingredients.length ? (
            meal.matched_ingredients.map((item) => (
              <span key={item} className="tag tag-ok">
                {item}
              </span>
            ))
          ) : (
            <span className="tag">None yet</span>
          )}
        </div>
      </div>
      <div className="meal-section">
        <p className="section-label">Missing ingredients</p>
        <div className="tag-list">
          {meal.missing_ingredients.length ? (
            meal.missing_ingredients.map((item) => (
              <span key={item} className="tag tag-warn">
                {item}
              </span>
            ))
          ) : (
            <span className="tag tag-ok">All set</span>
          )}
        </div>
      </div>
      {meal.missing_ingredients.length ? (
        <div className="meal-section">
          <p className="section-label">Substitutions</p>
          <ul className="sub-list">
            {meal.missing_ingredients.map((item) => {
              const options = meal.substitutions[item] || []
              const label = options.length ? options.join(', ') : 'No pantry swaps'
              return (
                <li key={item}>
                  <strong>{item}:</strong> {label}
                </li>
              )
            })}
          </ul>
        </div>
      ) : null}
    </article>
  )
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

function Meals() {
  const [data, setData] = useState<MealSuggestionsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadSuggestions = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getMealSuggestions()
      setData(response)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load meals.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSuggestions()
  }, [])

  return (
    <section className="page">
      <div className="page-header">
        <h1>Meals</h1>
        <p>Find ideas that use what you already have first.</p>
      </div>

      <section className="card">
        <div className="toolbar">
          <div>
            <h2>Items to use first</h2>
            <p className="muted">Urgency scores based on expiry and stock.</p>
          </div>
          <button type="button" className="button ghost" onClick={loadSuggestions}>
            Refresh
          </button>
        </div>

        {error ? <p className="status status-error">{error}</p> : null}
        {loading ? <p className="status status-wait">Loading suggestions...</p> : null}

        {!loading && data?.urgent_items.length ? (
          <div className="urgent-grid">
            {data.urgent_items.map((item) => (
              <UrgentItemChip key={item.id} item={item} />
            ))}
          </div>
        ) : null}

        {!loading && data?.urgent_items.length === 0 ? (
          <p className="empty">No pantry items found yet.</p>
        ) : null}
      </section>

      <section className="card">
        <h2>Cook today</h2>
        <div className="meals-grid">
          {data?.meals.cook_today.length ? (
            data.meals.cook_today.map((meal) => <MealCard key={meal.id} meal={meal} />)
          ) : (
            <p className="empty">No meals ready for today.</p>
          )}
        </div>
      </section>

      <section className="card">
        <h2>Cook this week</h2>
        <div className="meals-grid">
          {data?.meals.cook_this_week.length ? (
            data.meals.cook_this_week.map((meal) => (
              <MealCard key={meal.id} meal={meal} />
            ))
          ) : (
            <p className="empty">No weekly matches yet.</p>
          )}
        </div>
      </section>

      <section className="card">
        <h2>Possible later</h2>
        <div className="meals-grid">
          {data?.meals.possible_later.length ? (
            data.meals.possible_later.map((meal) => (
              <MealCard key={meal.id} meal={meal} />
            ))
          ) : (
            <p className="empty">No ideas queued yet.</p>
          )}
        </div>
      </section>
    </section>
  )
}

export default Meals
