import { api } from "./api";
import { EventOut, SOSOut } from "../types/api";

export interface TriggerSOSInput {
  device_id: string;
  reason?: string;
  latitude?: number;
  longitude?: number;
}

/**
 * Trigger a real SOS via the backend. There is no local/fake SOS path --
 * every SOS the guardian sends goes through POST /api/sos and is
 * persisted + dispatched through the backend's notification service.
 */
export async function triggerSOS(input: TriggerSOSInput): Promise<SOSOut> {
  const response = await api.post<SOSOut>("/api/sos", {
    device_id: input.device_id,
    reason: input.reason ?? "guardian_triggered",
    latitude: input.latitude,
    longitude: input.longitude,
  });
  return response.data;
}

/**
 * The backend doesn't (yet) have a dedicated "current SOS state" endpoint --
 * SOS events land in the generic event stream with source considerations
 * handled by the SOSEvent table, exposed indirectly through /api/events
 * only for source="manual"/similar. We surface SOS state to the UI via
 * the WebSocket "sos" message (see websocketService.ts) plus this
 * best-effort history read from the generic event log for anything the
 * stick itself reported as a fall/danger with risk_level="critical".
 */
export async function getRecentCriticalEvents(deviceId: string): Promise<EventOut[]> {
  const response = await api.get<EventOut[]>(`/api/events/${encodeURIComponent(deviceId)}`, {
    params: { risk_level: "critical", limit: 10 },
  });
  return response.data;
}
