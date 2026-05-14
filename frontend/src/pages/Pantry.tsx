import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react'
import {
  createPantryItem,
  deletePantryItem,
  listPantryItems,
  updatePantryItem,
  type PantryItem,
} from '../api/pantryApi'
import EmptyState from '../components/EmptyState'
import Toast from '../components/Toast'
import { useToast } from '../hooks/useToast'

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
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const { toast, showToast, clearToast } = useToast()

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

  useEffect(() => {
    setSelectedIds(new Set())
  }, [items])

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

  const categoryOptions = useMemo(() => {
    const unique = new Set<string>()
    items.forEach((item) => {
      if (item.category) {
        unique.add(item.category)
      }
    })
    return Array.from(unique).sort((a, b) => a.localeCompare(b))
  }, [items])

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
        showToast('Pantry item updated.', 'success')
      } else {
        await createPantryItem(payload)
        showToast('Pantry item added.', 'success')
      }
      resetForm()
      await loadItems()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Save failed.'
      setError(message)
      showToast(message, 'error')
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
      showToast('Pantry item deleted.', 'success')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Delete failed.'
      setError(message)
      showToast(message, 'error')
    }
  }

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    setSelectedIds((prev) => {
      if (filteredItems.length === 0) {
        return new Set()
      }
      if (prev.size === filteredItems.length) {
        return new Set()
      }
      return new Set(filteredItems.map((item) => item.id))
    })
  }

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) {
      return
    }

    const confirmed = window.confirm(
      `Delete ${selectedIds.size} selected item(s)?`
    )
    if (!confirmed) {
      return
    }

    try {
      await Promise.all(Array.from(selectedIds).map((id) => deletePantryItem(id)))
      await loadItems()
      showToast('Selected items deleted.', 'success')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Batch delete failed.'
      setError(message)
      showToast(message, 'error')
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
          <div className="toolbar-group">
            <button type="button" className="button ghost" onClick={loadItems}>
              Refresh
            </button>
            <button
              type="button"
              className="button danger"
              onClick={handleBatchDelete}
              disabled={selectedIds.size === 0}
            >
              Delete selected ({selectedIds.size})
            </button>
          </div>
        </div>

        {categoryOptions.length ? (
          <div className="chip-row">
            <button
              type="button"
              className={category === '' ? 'chip chip-active' : 'chip'}
              onClick={() => setCategory('')}
            >
              All
            </button>
            {categoryOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={category === option ? 'chip chip-active' : 'chip'}
                onClick={() => setCategory(option)}
              >
                {option}
              </button>
            ))}
          </div>
        ) : null}

        {error ? <p className="status status-error">{error}</p> : null}
        {loading ? (
          <div className="skeleton-table">
            <div className="skeleton-line wide" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
          </div>
        ) : null}

        {!loading && filteredItems.length === 0 ? (
          <EmptyState
            title="No pantry items yet"
            message="Add your first ingredients to start tracking expiry dates."
            action={
              <button type="button" className="button" onClick={() => window.scrollTo(0, 0)}>
                Add an item
              </button>
            }
          />
        ) : null}

        {filteredItems.length > 0 && !loading ? (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      checked={
                        selectedIds.size > 0 &&
                        selectedIds.size === filteredItems.length
                      }
                      onChange={toggleSelectAll}
                      aria-label="Select all items"
                    />
                  </th>
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
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(item.id)}
                          onChange={() => toggleSelect(item.id)}
                          aria-label={`Select ${item.name}`}
                        />
                      </td>
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
      <Toast toast={toast} onClose={clearToast} />
    </section>
  )
}

export default Pantry
