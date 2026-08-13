import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import * as deviceService from "../services/deviceService";
import { useAuth } from "./AuthContext";
import { PairedDevice } from "../types/api";

interface DeviceContextValue {
  devices: PairedDevice[];
  selectedDeviceId: string | null;
  selectedDevice: PairedDevice | null;
  isLoading: boolean;
  error: string | null;
  refreshDevices: () => Promise<void>;
  selectDevice: (deviceId: string) => void;
  applyLiveUpdate: (deviceId: string, patch: Partial<PairedDevice>) => void;
}

const DeviceContext = createContext<DeviceContextValue | undefined>(undefined);

export function DeviceProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [devices, setDevices] = useState<PairedDevice[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshDevices = useCallback(async () => {
    if (!isAuthenticated) return;
    setIsLoading(true);
    setError(null);
    try {
      const list = await deviceService.listPairedDevices();
      setDevices(list);
      setSelectedDeviceId((current) => current ?? list[0]?.device_id ?? null);
    } catch (err) {
      setError("Could not load your paired devices from the backend.");
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      refreshDevices();
    } else {
      setDevices([]);
      setSelectedDeviceId(null);
    }
  }, [isAuthenticated, refreshDevices]);

  const selectDevice = useCallback((deviceId: string) => {
    setSelectedDeviceId(deviceId);
  }, []);

  /** Merges a real-time WebSocket update into local state without another round trip. */
  const applyLiveUpdate = useCallback((deviceId: string, patch: Partial<PairedDevice>) => {
    setDevices((prev) =>
      prev.map((device) => (device.device_id === deviceId ? { ...device, ...patch } : device))
    );
  }, []);

  const selectedDevice = useMemo(
    () => devices.find((device) => device.device_id === selectedDeviceId) ?? null,
    [devices, selectedDeviceId]
  );

  const value = useMemo<DeviceContextValue>(
    () => ({
      devices,
      selectedDeviceId,
      selectedDevice,
      isLoading,
      error,
      refreshDevices,
      selectDevice,
      applyLiveUpdate,
    }),
    [devices, selectedDeviceId, selectedDevice, isLoading, error, refreshDevices, selectDevice, applyLiveUpdate]
  );

  return <DeviceContext.Provider value={value}>{children}</DeviceContext.Provider>;
}

export function useDevices(): DeviceContextValue {
  const ctx = useContext(DeviceContext);
  if (!ctx) throw new Error("useDevices must be used within a DeviceProvider");
  return ctx;
}
