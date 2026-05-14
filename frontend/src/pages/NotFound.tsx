import EmptyState from '../components/EmptyState'

function NotFound() {
  return (
    <section className="page">
      <div className="page-header">
        <h1>Page not found</h1>
        <p>We could not find that view. Try a navigation link above.</p>
      </div>
      <EmptyState
        title="Nothing to see here"
        message="Use the navigation to return to a valid PantryFlow page."
      />
    </section>
  )
}

export default NotFound
