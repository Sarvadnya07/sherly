/**
 * WEBSOCKET CLIENT SERVICE
 * Real-time event gateway for status, speech, and model events.
 */

import { SherlyEvent } from '../types/api';

type EventHandler = (event: SherlyEvent) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Set<EventHandler> = new Set();
  private reconnectTimer: any = null;

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.ws = new WebSocket('ws://127.0.0.1:8000/ws');

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected to Sherly backend');
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed: SherlyEvent = JSON.parse(event.data);
          this.handlers.forEach((handler) => handler(parsed));
        } catch (e) {
          console.warn('[WebSocket] Error parsing message:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('[WebSocket] Connection closed. Reconnecting in 3s...');
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.warn('[WebSocket] Connection error:', error);
      };
    } catch (e) {
      console.error('[WebSocket] Failed to establish connection:', e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 3000);
    }
  }

  public subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  public send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export const wsService = new WebSocketService();
