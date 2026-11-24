import { useRef, useState, useCallback, useEffect } from "react"

type WSStatus = "disconnected" | "connecting" | "connected" | "error"

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const [status, setStatus] = useState<WSStatus>("disconnected")
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    setStatus("connecting")
    const backendUrl = import.meta.env.VITE_BACKEND_URL
    let wsUrl: string
    if (backendUrl) {
      const cleanUrl = backendUrl.replace(/\/$/, "")
      const wsProto = cleanUrl.startsWith("https") ? "wss:" : "ws:"
      const host = cleanUrl.replace(/^https?:\/\//, "")
      wsUrl = `${wsProto}//${host}/ws/transcribe`
    } else {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:"
      wsUrl = `${proto}//${window.location.host}/ws/transcribe`
    }
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => setStatus("connected")
    ws.onmessage = (e) => {
      try { setLastMessage(JSON.parse(e.data)) } catch { /* ignore */ }
    }
    ws.onerror = () => setStatus("error")
    ws.onclose = () => setStatus("disconnected")
    wsRef.current = ws
  }, [])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
    setStatus("disconnected")
  }, [])

  const sendMessage = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  useEffect(() => () => { wsRef.current?.close() }, [])

  return { status, lastMessage, connect, disconnect, sendMessage }
}
