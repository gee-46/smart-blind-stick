import { api } from "./api";
import { LocationHistoryItem, LocationPoint } from "../types/api";

export async function getLatestLocation(deviceId: string): Promise<LocationPoint> {
  const response = await api.get<LocationPoint>(`/api/location/${encodeURIComponent(deviceId)}`);
  return response.data;
}

export async function getLocationHistory(deviceId: string, limit = 50): Promise<LocationHistoryItem[]> {
  const response = await api.get<LocationHistoryItem[]>(
    `/api/location/${encodeURIComponent(deviceId)}/history`,
    { params: { limit } }
  );
  return response.data;
}
