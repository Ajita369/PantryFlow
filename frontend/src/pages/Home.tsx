import { useEffect, useState } from 'react'

type HealthResponse = {
  status: string
}

function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    fetch('/api/health/')
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Health check failed')
        }
        return response.json() as Promise<HealthResponse>
      })
      .then((data) => {
        if (isMounted) {
          setHealth(data)
        }
      })
      .catch((err: Error) => {
        if (isMounted) {
          setError(err.message)
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <section className="page">
      <div className="page-header">
        <h1>Welcome to PantryFlow</h1>
        <p>
          Track what you already have, plan meals around what is expiring, and
          stay on budget with confident grocery decisions.
        </p>
      </div>

      <div className="grid">
        <article className="card">
          <h2>Backend status</h2>
          {error ? (
            <p className="status status-error">{error}</p>
          ) : health ? (
            <p className="status status-ok">Status: {health.status}</p>
          ) : (
            <p className="status status-wait">Checking /api/health/...</p>
          )}
        </article>
        <article className="card">
          <h2>Today&apos;s focus</h2>
          <p>See what is expiring soon and schedule meals around it.</p>
        </article>
        <article className="card">
          <h2>Budget snapshot</h2>
          <p>Set a weekly target and keep spending on track.</p>
        </article>
      </div>

      <section className="callout">
        <div>
          <h2>Next step</h2>
          <p>Head to Pantry to add items and start planning.</p>
        </div>
        <div className="callout-accent">Phase 1 ready</div>
      </section>
    </section>
  )
}

export default Home
