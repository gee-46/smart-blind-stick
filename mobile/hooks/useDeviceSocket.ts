import { useEffect, useRef, useState } from "react";

import { DeviceSocket, WSStatus } from "../services/websocketService";
import { WSMessage } from "../types/api";

/**
 * Subscribes to the real-time relay for a device and returns the most
 * recent message of each type seen, plus connection status. Handles
 * connect/disconnect lifecycle and reconnect automatically.
 */
export function useDeviceSocket(deviceId: string | null, onMessage?: (message: WSMessage) => void) {
  const [status, setStatus] = useState<WSStatus>("closed");
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const socketRef = useRef<DeviceSocket | null>(null);

  useEffect(() => {
    if (!deviceId) return;

    const socket = new DeviceSocket(deviceId);
    socketRef.current = socket;

    const unsubscribeStatus = socket.onStatusChange(setStatus);
    const unsubscribeMessage = socket.onMessage((message) => {
      setLastMessage(message);
      onMessage?.(message);
    });

    socket.connect();

    return () => {
      unsubscribeStatus();
      unsubscribeMessage();
      socket.disconnect();
      socketRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId]);

  return { status, lastMessage };
}
