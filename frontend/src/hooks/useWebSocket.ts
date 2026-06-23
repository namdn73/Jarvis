import { useEffect, useRef, useState } from 'react'
import type { WsMessage } from '../types'

export function useWebSocket(dispatch: React.Dispatch<WsMessage>): { connected: boolean } {
  const [connected, setConnected] = useState(false)
  const unmountedRef = useRef(false)

  useEffect(() => {
    unmountedRef.current = false

    function connect() {
      if (unmountedRef.current) return

      const ws = new WebSocket(`ws://${window.location.host}/ws`)

      ws.onopen = () => setConnected(true)

      ws.onmessage = (event: MessageEvent) => {
        try {
          const message = JSON.parse(event.data as string) as WsMessage
          dispatch(message)
        } catch (e) {
          console.error('[WS] parse error', e)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        if (!unmountedRef.current) {
          setTimeout(connect, 2000)
        }
      }
    }

    connect()

    return () => {
      unmountedRef.current = true
    }
  }, [dispatch])

  return { connected }
}
