import type { ReactNode } from 'react'

const DefaultIcon = () => (
  <svg
    className="empty-icon"
    viewBox="0 0 48 48"
    role="img"
    aria-hidden="true"
    focusable="false"
  >
    <rect x="6" y="10" width="36" height="28" rx="6" />
    <path d="M14 20h20M14 26h14M14 32h10" />
  </svg>
)

type EmptyStateProps = {
  title: string
  message: string
  action?: ReactNode
}

function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <DefaultIcon />
      <div>
        <h3>{title}</h3>
        <p>{message}</p>
        {action ? <div className="empty-actions">{action}</div> : null}
      </div>
    </div>
  )
}

export default EmptyState
