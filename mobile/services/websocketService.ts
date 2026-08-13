/**
 * Real-time WebSocket client for /ws/device/{device_id}.
 *
 * Handles: connection with JWT auth, exponential-backoff reconnect,
 * app-level heartbeat, and typed message dispatch. Every message this
 * emits came from the real backend relay (see app/websocket_manager.py
 * and the hooks in app/services/device_service.py / event_service.py) --
 * this client never invents events.
 */
import { API_BASE_URL } from "./api";
import { getAccessToken } from "../utils/tokenStorage";
import { WSMessage } from "../types/api";

export type WSStatus = "connecting" | "open" | "closed" | "error";

type Listener = (message: WSMessage) => void;
type StatusListener = (status: WSStatus) => void;

const HEARTBEAT_INTERVAL_MS = 25000;
const MAX_BACKOFF_MS = 30000;

export class DeviceSocket {
  private socket: WebSocket | null = null;
  private deviceId: string;
  private listeners = new Set<Listener>();
  private statusListeners = new Set<StatusListener>();
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempt = 0;
  private manuallyClosed = false;

  constructor(deviceId: string) {
    this.deviceId = deviceId;
  }

  onMessage(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onStatusChange(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    return () => this.statusListeners.delete(listener);
  }

  private emitStatus(status: WSStatus) {
    this.statusListeners.forEach((l) => l(status));
  }

  async connect(): Promise<void> {
    this.manuallyClosed = false;
    const token = await getAccessToken();
    if (!token) {
      this.emitStatus("error");
      return;
    }

    const wsUrl = API_BASE_URL.replace(/^http/, "ws");
    const url = `${wsUrl}/ws/device/${encodeURIComponent(this.deviceId)}?token=${encodeURIComponent(token)}`;

    this.emitStatus("connecting");
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      this.reconnectAttempt = 0;
      this.emitStatus("open");
      this.startHeartbeat();
    };

    this.socket.onmessage = (event: WebSocketMessageEvent) => {
      try {
        const data = JSON.parse(event.data) as WSMessage;
        if (data.type === "connected") return; // internal ack, not a UI event
        this.listeners.forEach((listener) => listener(data));
      } catch {
        // Non-JSON frame (e.g. our own "pong" text) -- ignore.
      }
    };

    this.socket.onerror = () => {
      this.emitStatus("error");
    };

    this.socket.onclose = () => {
      this.stopHeartbeat();
      this.emitStatus("closed");
      if (!this.manuallyClosed) {
        this.scheduleReconnect();
      }
    };
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send("ping");
      }
    }, HEARTBEAT_INTERVAL_MS);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect() {
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, MAX_BACKOFF_MS);
    this.reconnectAttempt += 1;
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect(): void {
    this.manuallyClosed = true;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }
}
