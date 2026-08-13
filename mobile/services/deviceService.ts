import { api } from "./api";
import { DeviceStatus, PairedDevice } from "../types/api";

export async function pairDevice(deviceId: string, nickname?: string): Promise<PairedDevice> {
  const response = await api.post<PairedDevice>("/api/guardian/devices", {
    device_id: deviceId,
    nickname: nickname || undefined,
  });
  return response.data;
}

export async function listPairedDevices(): Promise<PairedDevice[]> {
  const response = await api.get<PairedDevice[]>("/api/guardian/devices");
  return response.data;
}

export async function unpairDevice(deviceId: string): Promise<void> {
  await api.delete(`/api/guardian/devices/${encodeURIComponent(deviceId)}`);
}

/** Raw device status straight from the smart-stick-facing endpoint (used for a manual refresh). */
export async function getDeviceStatus(deviceId: string): Promise<DeviceStatus> {
  const response = await api.get<DeviceStatus>(`/api/device/status/${encodeURIComponent(deviceId)}`);
  return response.data;
}
