/**
 * WEBSOCKET CLIENT SERVICE — frontend/src/services/websocket.ts
 * Real-time event gateway for status, speech, action, and model events.
 * Features: Exponential backoff reconnection, safe error handling, and typed listener dispatch.
 */

import { SherlyEvent } from '../types/api';

type EventHandler = (event: SherlyEvent) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Set<EventHandler> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectDelayMs = 10000;
  private baseReconnectDelayMs = 1000;

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const wsUrl = (import.meta.env.VITE_WS_URL as string | undefined) || 'ws://127.0.0.1:8000/ws';
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected to Sherly backend');
        this.reconnectAttempts = 0;
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed: SherlyEvent = JSON.parse(event.data);
          if (!parsed || !parsed.event_type) {
            console.warn('[WebSocket] Received malformed event payload:', event.data);
            return;
          }
          this.handlers.forEach((handler) => {
            try {
              handler(parsed);
            } catch (err) {
              console.error('[WebSocket] Error in event listener handler:', err);
            }
          });
        } catch (e) {
          console.warn('[WebSocket] Failed to parse incoming JSON frame:', e);
        }
      };

      this.ws.onclose = () => {
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.warn('[WebSocket] Transport error:', error);
      };
    } catch (e) {
      console.error('[WebSocket] Failed to instantiate connection:', e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;

    // Exponential backoff with jitter
    const delay = Math.min(
      this.baseReconnectDelayMs * Math.pow(1.5, this.reconnectAttempts) + Math.random() * 500,
      this.maxReconnectDelayMs
    );
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  public subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  public disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }

  public send(data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export const wsService = new WebSocketService();
