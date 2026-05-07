import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react'
import {
  createPantryItem,
  deletePantryItem,
  listPantryItems,
  updatePantryItem,
  type PantryItem,
} from '../api/pantryApi'

type PantryFormState = {
  name: string
  category: string
  quantity: string
  unit: string
  expiry_date: string
  purchase_date: string
  notes: string
  location: string
}

type UrgencyFilter = 'all' | 'expired' | 'soon' | 'ok' | 'no-expiry'

const initialForm: PantryFormState = {
  name: '',
  category: '',
  quantity: '',
  unit: '',
  expiry_date: '',
  purchase_date: '',
  notes: '',
  location: '',
}

function getUrgencyLabel(item: PantryItem) {
  if (!item.expiry_date) {
    return { label: 'No expiry', tone: 'badge-muted' }
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expiry = new Date(`${item.expiry_date}T00:00:00`)
  const diffMs = expiry.getTime() - today.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return { label: 'Expired', tone: 'badge-danger' }
  }
  if (diffDays <= 3) {
    return { label: 'Urgent', tone: 'badge-warning' }
  }
  if (diffDays <= 7) {
    return { label: 'Soon', tone: 'badge-warning' }
  }

  return { label: 'OK', tone: 'badge-ok' }
}

function Pantry() {
  const [items, setItems] = useState<PantryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formState, setFormState] = useState<PantryFormState>(initialForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [urgency, setUrgency] = useState<UrgencyFilter>('all')

  const loadItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listPantryItems({
        search: search.trim() || undefined,
        category: category.trim() || undefined,
      })
      setItems(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load items.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadItems()
  }, [search, category])

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (urgency === 'all') {
        return true
      }

      const urgencyInfo = getUrgencyLabel(item)
      if (urgency === 'expired') {
        return urgencyInfo.label === 'Expired'
      }
      if (urgency === 'soon') {
        return urgencyInfo.label === 'Urgent' || urgencyInfo.label === 'Soon'
      }
      if (urgency === 'ok') {
        return urgencyInfo.label === 'OK'
      }
      return urgencyInfo.label === 'No expiry'
    })
  }, [items, urgency])

  const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const resetForm = () => {
    setFormState(initialForm)
    setEditingId(null)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    const payload = {
      name: formState.name.trim(),
      category: formState.category.trim(),
      quantity: Number(formState.quantity),
      unit: formState.unit.trim(),
      expiry_date: formState.expiry_date || null,
      purchase_date: formState.purchase_date || null,
      notes: formState.notes.trim(),
      location: formState.location.trim(),
    }

    try {
      if (editingId) {
        await updatePantryItem(editingId, payload)
      } else {
        await createPantryItem(payload)
      }
      resetForm()
      await loadItems()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Save failed.'
      setError(message)
    }
  }

  const handleEdit = (item: PantryItem) => {
    setFormState({
      name: item.name,
      category: item.category || '',
      quantity: item.quantity,
      unit: item.unit || '',
      expiry_date: item.expiry_date || '',
      purchase_date: item.purchase_date || '',
      notes: item.notes || '',
      location: item.location || '',
    })
    setEditingId(item.id)
  }

  const handleDelete = async (item: PantryItem) => {
    const confirmed = window.confirm(`Delete ${item.name}?`)
    if (!confirmed) {
      return
    }

    try {
      await deletePantryItem(item.id)
      await loadItems()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Delete failed.'
      setError(message)
    }
  }

  return (
    <section className="page">
      <div className="page-header">
        <h1>Pantry</h1>
        <p>Add items, track quantities, and monitor expiry dates.</p>
      </div>

      <section className="card">
        <h2>{editingId ? 'Edit item' : 'Add item'}</h2>
        <form className="form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="field">
              <span>Name</span>
              <input
                name="name"
                value={formState.name}
                onChange={handleChange}
                placeholder="Brown rice"
                required
              />
            </label>
            <label className="field">
              <span>Category</span>
              <input
                name="category"
                value={formState.category}
                onChange={handleChange}
                placeholder="Grains"
              />
            </label>
            <label className="field">
              <span>Quantity</span>
              <input
                name="quantity"
                value={formState.quantity}
                onChange={handleChange}
                placeholder="2"
                type="number"
                min="0"
                step="0.01"
                required
              />
            </label>
            <label className="field">
              <span>Unit</span>
              <input
                name="unit"
                value={formState.unit}
                onChange={handleChange}
                placeholder="kg"
              />
            </label>
            <label className="field">
              <span>Expiry date</span>
              <input
                name="expiry_date"
                value={formState.expiry_date}
                onChange={handleChange}
                type="date"
              />
            </label>
            <label className="field">
              <span>Purchase date</span>
              <input
                name="purchase_date"
                value={formState.purchase_date}
                onChange={handleChange}
                type="date"
              />
            </label>
            <label className="field">
              <span>Location</span>
              <input
                name="location"
                value={formState.location}
                onChange={handleChange}
                placeholder="Pantry"
              />
            </label>
            <label className="field field-span">
              <span>Notes</span>
              <textarea
                name="notes"
                value={formState.notes}
                onChange={handleChange}
                placeholder="Open bag on top shelf"
                rows={3}
              />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="button">
              {editingId ? 'Update item' : 'Add item'}
            </button>
            {editingId ? (
              <button type="button" className="button ghost" onClick={resetForm}>
                Cancel
              </button>
            ) : null}
          </div>
        </form>
      </section>

      <section className="card">
        <div className="toolbar">
          <div className="toolbar-group">
            <label className="field">
              <span>Search</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by name or category"
              />
            </label>
            <label className="field">
              <span>Category</span>
              <input
                value={category}
                onChange={(event) => setCategory(event.target.value)}
                placeholder="All categories"
              />
            </label>
            <label className="field">
              <span>Urgency</span>
              <select
                value={urgency}
                onChange={(event) => setUrgency(event.target.value as UrgencyFilter)}
              >
                <option value="all">All</option>
                <option value="expired">Expired</option>
                <option value="soon">Expiring soon</option>
                <option value="ok">OK</option>
                <option value="no-expiry">No expiry</option>
              </select>
            </label>
          </div>
          <button type="button" className="button ghost" onClick={loadItems}>
            Refresh
          </button>
        </div>

        {error ? <p className="status status-error">{error}</p> : null}
        {loading ? <p className="status status-wait">Loading pantry...</p> : null}

        {!loading && filteredItems.length === 0 ? (
          <p className="empty">No pantry items found yet.</p>
        ) : null}

        {filteredItems.length > 0 ? (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Quantity</th>
                  <th>Category</th>
                  <th>Location</th>
                  <th>Expiry</th>
                  <th>Urgency</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => {
                  const urgencyInfo = getUrgencyLabel(item)
                  return (
                    <tr key={item.id}>
                      <td>{item.name}</td>
                      <td>
                        {item.quantity} {item.unit}
                      </td>
                      <td>{item.category || '-'}</td>
                      <td>{item.location || '-'}</td>
                      <td>{item.expiry_date || 'No expiry'}</td>
                      <td>
                        <span className={`badge ${urgencyInfo.tone}`}>
                          {urgencyInfo.label}
                        </span>
                      </td>
                      <td className="actions">
                        <button
                          type="button"
                          className="button ghost"
                          onClick={() => handleEdit(item)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="button danger"
                          onClick={() => handleDelete(item)}
                        >
                          Delete
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

export default Pantry
