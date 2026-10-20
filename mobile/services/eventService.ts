import { api } from "./api";
import { EventOut } from "../types/api";

export interface EventFilters {
  event_type?: string;
  risk_level?: string;
  date?: string; // ISO date, e.g. "2026-08-13"
  limit?: number;
}

export async function getEvents(deviceId: string, filters: EventFilters = {}): Promise<EventOut[]> {
  const response = await api.get<EventOut[]>(`/api/events/${encodeURIComponent(deviceId)}`, {
    params: filters,
  });
  return response.data;
}

/** Convenience: only the most recent event, used to drive the dashboard's "latest event" cards. */
export async function getLatestEvent(deviceId: string, source?: string): Promise<EventOut | null> {
  const events = await getEvents(deviceId, { limit: source ? 20 : 1 });
  if (!source) return events[0] ?? null;
  return events.find((event) => event.source === source) ?? null;
}
