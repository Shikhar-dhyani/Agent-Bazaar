import { useEffect, useRef, useCallback } from 'react'
import type { WSEvent } from '../types'

const WS_BASE = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'

export function useWebSocket(
  taskId: string | null,
  onEvent: (event: WSEvent) => void,
) {
  const wsRef = useRef<WebSocket | null>(null)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    if (!taskId) return

    const ws = new WebSocket(`${WS_BASE}/ws/${taskId}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      try {
        const event: WSEvent = JSON.parse(e.data)
        onEventRef.current(event)
      } catch {
        // ignore malformed frames
      }
    }

    ws.onerror = () => {
      // silently handle connection errors
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [taskId])
}
