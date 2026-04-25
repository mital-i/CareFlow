import { useEffect, useRef, useState } from 'react'

export function useSSE(url, onMessage) {
  const [connected, setConnected] = useState(false)
  const esRef = useRef(null)

  useEffect(() => {
    if (!url) return
    const es = new EventSource(url)
    esRef.current = es
    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)
    es.onmessage = (e) => onMessage(JSON.parse(e.data))
    return () => es.close()
  }, [url])

  return { connected }
}
