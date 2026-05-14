import { useEffect, useState } from 'react'
import type { ToastState } from '../components/Toast'

type UseToastResult = {
  toast: ToastState | null
  showToast: (message: string, tone?: ToastState['tone']) => void
  clearToast: () => void
}

export function useToast(duration = 3200): UseToastResult {
  const [toast, setToast] = useState<ToastState | null>(null)

  useEffect(() => {
    if (!toast) {
      return
    }

    const timeout = window.setTimeout(() => {
      setToast(null)
    }, duration)

    return () => {
      window.clearTimeout(timeout)
    }
  }, [toast, duration])

  const showToast = (message: string, tone: ToastState['tone'] = 'info') => {
    setToast({ message, tone })
  }

  const clearToast = () => setToast(null)

  return { toast, showToast, clearToast }
}
