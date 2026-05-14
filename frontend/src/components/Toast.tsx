export type ToastState = {
  message: string
  tone?: 'success' | 'error' | 'info'
}

type ToastProps = {
  toast: ToastState | null
  onClose?: () => void
}

function Toast({ toast, onClose }: ToastProps) {
  if (!toast) {
    return null
  }

  return (
    <div className={`toast toast-${toast.tone ?? 'info'}`} role="status" aria-live="polite">
      <span>{toast.message}</span>
      {onClose ? (
        <button type="button" className="toast-close" onClick={onClose} aria-label="Close">
          Close
        </button>
      ) : null}
    </div>
  )
}

export default Toast
