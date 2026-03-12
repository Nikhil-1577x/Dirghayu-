/**
 * WebSocket connection to backend for real-time updates.
 */
import { useEffect, useRef } from 'react';
import { getWsUrl } from './client';
import { useApiStore } from '../store';
import { useWSStore } from '../store';

export function useWebSocket() {
  const patientId = useApiStore((s) => s.patientId);
  const setStatus = useWSStore((s) => s.setStatus);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!patientId) {
      setStatus('disconnected');
      return;
    }

    const url = getWsUrl(patientId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setStatus('connected');
    ws.onclose = () => setStatus('disconnected');
    ws.onerror = () => setStatus('reconnecting');

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === 'dose_event') {
          // Could update medication store here
        }
        if (data.type === 'risk_update') {
          // Could update risk score
        }
      } catch {
        // ignore parse errors
      }
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 30000);

    return () => {
      clearInterval(ping);
      ws.close();
      wsRef.current = null;
      setStatus('disconnected');
    };
  }, [patientId, setStatus]);

  return null;
}
