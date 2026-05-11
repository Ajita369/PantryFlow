import { useEffect, useState, type Dispatch, type SetStateAction } from 'react'
import {
  getMealExplanation,
  getSubstitutionHelp,
  type AiResponse,
} from '../api/aiApi'
import {
  generateMeals,
  getMealSuggestions,
  type MealSuggestion,
  type MealSuggestionsResponse,
  type UrgentItem,
} from '../api/mealsApi'
import { addShoppingItems } from '../api/planningApi'

type AiNoteState = {
  message?: string
  error?: string
  loading?: boolean
  source?: string
  fallback?: boolean
}

type MealCardProps = {
  meal: MealSuggestion
  noteState?: AiNoteState
  substitutionState?: AiNoteState
  shoppingState?: AiNoteState
  onMealNote: (meal: MealSuggestion) => void
  onSubstitutionNote: (meal: MealSuggestion) => void
  onAddToShopping: (meal: MealSuggestion) => void
}

function MealCard({
  meal,
  noteState,
  substitutionState,
  shoppingState,
  onMealNote,
  onSubstitutionNote,
  onAddToShopping,
}: MealCardProps) {
  return (
    <article className="meal-card">
      <div className="meal-header">
        <div>
          <h3>{meal.title}</h3>
          <p className="muted">{meal.description}</p>
        </div>
        <div className="meal-badges">
          <span className={`meal-source meal-source-${meal.source}`}>{meal.source}</span>
          <span className="meal-score">Match {Math.round(meal.match_score * 100)}%</span>
        </div>
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
      {meal.missing_ingredients.length ? (
        <div className="shopping-hint">
          <p>Buy missing items from the Shopping List to complete this meal.</p>
          <button
            type="button"
            className="button ghost"
            onClick={() => onAddToShopping(meal)}
            disabled={shoppingState?.loading}
          >
            {shoppingState?.loading ? 'Adding...' : 'Add missing to shopping list'}
          </button>
          {shoppingState?.error ? (
            <span className="ai-status ai-error">{shoppingState.error}</span>
          ) : shoppingState?.message ? (
            <span className="ai-status">{shoppingState.message}</span>
          ) : null}
        </div>
      ) : null}
      <details className="meal-steps">
        <summary>Steps</summary>
        {meal.steps.length ? (
          <ol>
            {meal.steps.map((step, index) => (
              <li key={`${meal.id}-step-${index}`}>{step}</li>
            ))}
          </ol>
        ) : (
          <p className="muted">No steps provided.</p>
        )}
      </details>
      <div className="meal-actions">
        <button
          type="button"
          className="button ghost"
          onClick={() => onMealNote(meal)}
        >
          Meal note
        </button>
        {meal.missing_ingredients.length ? (
          <button
            type="button"
            className="button ghost"
            onClick={() => onSubstitutionNote(meal)}
          >
            Substitution help
          </button>
        ) : null}
      </div>
      {noteState?.loading ? (
        <p className="ai-status">Loading meal note...</p>
      ) : noteState?.error ? (
        <p className="ai-status ai-error">{noteState.error}</p>
      ) : noteState?.message ? (
        <div className="ai-panel">
          <p>{noteState.message}</p>
          <span className="ai-meta">
            Source: {noteState.source}
            {noteState.fallback ? ' (fallback)' : ''}
          </span>
        </div>
      ) : null}
      {substitutionState?.loading ? (
        <p className="ai-status">Loading substitution help...</p>
      ) : substitutionState?.error ? (
        <p className="ai-status ai-error">{substitutionState.error}</p>
      ) : substitutionState?.message ? (
        <div className="ai-panel">
          <p>{substitutionState.message}</p>
          <span className="ai-meta">
            Source: {substitutionState.source}
            {substitutionState.fallback ? ' (fallback)' : ''}
          </span>
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
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mealNotes, setMealNotes] = useState<Record<number, AiNoteState>>({})
  const [subNotes, setSubNotes] = useState<Record<number, AiNoteState>>({})
  const [shoppingNotes, setShoppingNotes] = useState<Record<number, AiNoteState>>({})

  const formatGeneratedAt = (value?: string) => {
    if (!value) {
      return 'Not generated yet'
    }
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return value
    }
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date)
  }

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

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)
    try {
      const response = await generateMeals()
      setData(response)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate meals.'
      setError(message)
    } finally {
      setGenerating(false)
    }
  }

  const updateNoteState = (
    setter: Dispatch<SetStateAction<Record<number, AiNoteState>>>,
    mealId: number,
    next: AiNoteState
  ) => {
    setter((prev) => ({ ...prev, [mealId]: next }))
  }

  const requestMealNote = async (meal: MealSuggestion) => {
    updateNoteState(setMealNotes, meal.id, { loading: true })
    try {
      const response: AiResponse = await getMealExplanation(meal)
      updateNoteState(setMealNotes, meal.id, {
        message: response.message,
        source: response.source,
        fallback: response.fallback,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'AI note failed.'
      updateNoteState(setMealNotes, meal.id, { error: message })
    }
  }

  const requestSubNote = async (meal: MealSuggestion) => {
    updateNoteState(setSubNotes, meal.id, { loading: true })
    try {
      const response: AiResponse = await getSubstitutionHelp(meal)
      updateNoteState(setSubNotes, meal.id, {
        message: response.message,
        source: response.source,
        fallback: response.fallback,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'AI help failed.'
      updateNoteState(setSubNotes, meal.id, { error: message })
    }
  }

  const addMissingItemsToShopping = async (meal: MealSuggestion) => {
    updateNoteState(setShoppingNotes, meal.id, { loading: true })
    try {
      await addShoppingItems(meal.missing_ingredients)
      updateNoteState(setShoppingNotes, meal.id, {
        message: 'Added to Shopping List.',
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not update shopping list.'
      updateNoteState(setShoppingNotes, meal.id, { error: message })
    }
  }

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
            {data ? (
              <p className="muted">
                Last generated: {formatGeneratedAt(data.generated_at)}
                {data.cached ? ' (cached)' : ''}
              </p>
            ) : null}
          </div>
          <div className="toolbar-group">
            <button type="button" className="button ghost" onClick={loadSuggestions}>
              Refresh
            </button>
            <button
              type="button"
              className="button"
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? 'Generating...' : 'Generate new meals'}
            </button>
          </div>
        </div>

        {error ? <p className="status status-error">{error}</p> : null}
        {data?.llm_error ? (
          <p className="status status-warn">LLM fallback: {data.llm_error}</p>
        ) : null}
        {data?.pantry_changed ? (
          <div className="status status-warn">
            <span>Pantry updated since the last generation.</span>
            <button
              type="button"
              className="button ghost"
              onClick={handleGenerate}
              disabled={generating}
            >
              Regenerate now
            </button>
          </div>
        ) : null}
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
            data.meals.cook_today.map((meal) => (
              <MealCard
                key={meal.id}
                meal={meal}
                noteState={mealNotes[meal.id]}
                substitutionState={subNotes[meal.id]}
                shoppingState={shoppingNotes[meal.id]}
                onMealNote={requestMealNote}
                onSubstitutionNote={requestSubNote}
                onAddToShopping={addMissingItemsToShopping}
              />
            ))
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
              <MealCard
                key={meal.id}
                meal={meal}
                noteState={mealNotes[meal.id]}
                substitutionState={subNotes[meal.id]}
                shoppingState={shoppingNotes[meal.id]}
                onMealNote={requestMealNote}
                onSubstitutionNote={requestSubNote}
                onAddToShopping={addMissingItemsToShopping}
              />
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
              <MealCard
                key={meal.id}
                meal={meal}
                noteState={mealNotes[meal.id]}
                substitutionState={subNotes[meal.id]}
                shoppingState={shoppingNotes[meal.id]}
                onMealNote={requestMealNote}
                onSubstitutionNote={requestSubNote}
                onAddToShopping={addMissingItemsToShopping}
              />
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
