import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/pantry', label: 'Pantry' },
  { to: '/meals', label: 'Meals' },
  { to: '/shopping-list', label: 'Shopping List' },
  { to: '/budget', label: 'Budget' },
  { to: '/planner', label: 'Planner' },
]

function RootLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">PF</span>
          <div>
            <p className="brand-title">PantryFlow</p>
            <p className="brand-subtitle">AI Pantry Waste Reducer</p>
          </div>
        </div>
        <nav className="app-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                isActive ? 'nav-link nav-link-active' : 'nav-link'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        <p>Built to keep your pantry on track.</p>
      </footer>
    </div>
  )
}

export default RootLayout
