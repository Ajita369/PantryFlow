import { useEffect, useState } from 'react'
import {
  generateShoppingList,
  getShoppingList,
  updateShoppingItem,
  type ShoppingListItem,
  type ShoppingTotals,
} from '../api/planningApi'

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

function ShoppingList() {
  const [items, setItems] = useState<ShoppingListItem[]>([])
  const [totals, setTotals] = useState<ShoppingTotals | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadList = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getShoppingList()
      setItems(response.items)
      setTotals(response.totals)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load list.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadList()
  }, [])

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await generateShoppingList()
      setItems(response.items)
      setTotals(response.totals)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Generate failed.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (item: ShoppingListItem) => {
    try {
      await updateShoppingItem(item.id, { is_needed: !item.is_needed })
      setItems((prev) =>
        prev.map((entry) =>
          entry.id === item.id ? { ...entry, is_needed: !entry.is_needed } : entry
        )
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Update failed.'
      setError(message)
    }
  }

  const currency = totals?.currency || 'USD'

  return (
    <section className="page">
      <div className="page-header">
        <h1>Shopping List</h1>
        <p>Generate a prioritized list with estimated costs.</p>
      </div>

      <section className="card">
        <div className="toolbar">
          <div>
            <h2>Recommendations</h2>
            <p className="muted">
              Budget-aware items based on pantry stock.
            </p>
          </div>
          <div className="toolbar-group">
            <button type="button" className="button ghost" onClick={loadList}>
              Refresh
            </button>
            <button type="button" className="button" onClick={handleGenerate}>
              Generate list
            </button>
          </div>
        </div>

        <div className="summary-row">
          <div className="summary-card">
            <span>Total estimated</span>
            <strong>{formatCurrency(totals?.total_estimated_cost, currency)}</strong>
          </div>
          <div className="summary-card">
            <span>Budget remaining</span>
            <strong>{formatCurrency(totals?.budget_remaining, currency)}</strong>
          </div>
        </div>

        {error ? <p className="status status-error">{error}</p> : null}
        {loading ? <p className="status status-wait">Loading list...</p> : null}

        {!loading && items.length === 0 ? (
          <p className="empty">No shopping items yet. Generate a list to start.</p>
        ) : null}

        {items.length > 0 ? (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Qty</th>
                  <th>Priority</th>
                  <th>Estimated</th>
                  <th>Needed</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const label = priorityLabel[item.priority] ?? 'Medium'
                  return (
                    <tr key={item.id}>
                      <td>
                        <div className="item-name">
                          {item.name}
                          {item.reason ? (
                            <span className="item-reason">{item.reason}</span>
                          ) : null}
                        </div>
                      </td>
                      <td>
                        {item.quantity} {item.unit}
                      </td>
                      <td>
                        <span className={`badge badge-${label.toLowerCase()}`}>{label}</span>
                      </td>
                      <td>{formatCurrency(item.estimated_price, currency)}</td>
                      <td>
                        <button
                          type="button"
                          className={item.is_needed ? 'pill on' : 'pill'}
                          onClick={() => handleToggle(item)}
                        >
                          {item.is_needed ? 'Needed' : 'Got it'}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </section>
  )
}

export default ShoppingList
