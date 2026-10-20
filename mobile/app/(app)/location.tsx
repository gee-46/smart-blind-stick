import React, { useCallback, useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { ScreenShell } from "../../components/ScreenShell";
import { Card } from "../../components/Card";
import { LocationMap } from "../../components/LocationMap";
import { useDevices } from "../../context/DeviceContext";
import { useDeviceSocket } from "../../hooks/useDeviceSocket";
import * as locationService from "../../services/locationService";
import { extractErrorMessage } from "../../services/api";
import { colors, spacing, typography } from "../../utils/theme";
import { formatTimestamp } from "../../utils/format";
import { LocationHistoryItem, LocationPoint, WSMessage } from "../../types/api";

export default function LocationScreen() {
  const { selectedDevice } = useDevices();
  const [current, setCurrent] = useState<LocationPoint | null>(null);
  const [history, setHistory] = useState<LocationHistoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!selectedDevice) return;
    setIsLoading(true);
    setError(null);
    try {
      const [latest, hist] = await Promise.all([
        locationService.getLatestLocation(selectedDevice.device_id),
        locationService.getLocationHistory(selectedDevice.device_id, 50),
      ]);
      setCurrent(latest);
      setHistory(hist);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load location data."));
    } finally {
      setIsLoading(false);
    }
  }, [selectedDevice]);

  useEffect(() => {
    load();
  }, [load]);

  const handleWsMessage = useCallback(
    (message: WSMessage) => {
      if (message.type === "location_update" && selectedDevice) {
        setCurrent((prev) => ({
          device_id: selectedDevice.device_id,
          latitude: message.latitude as number,
          longitude: message.longitude as number,
          altitude: prev?.altitude ?? null,
          speed_kmh: prev?.speed_kmh ?? null,
          satellites: prev?.satellites ?? null,
          fix_quality: prev?.fix_quality ?? null,
          timestamp: message.timestamp as string,
        }));
      }
    },
    [selectedDevice]
  );

  useDeviceSocket(selectedDevice?.device_id ?? null, handleWsMessage);

  if (!selectedDevice) {
    return (
      <ScreenShell>
        <Card>
          <Text style={styles.emptyText}>Pair a device first to see its location.</Text>
        </Card>
      </ScreenShell>
    );
  }

  return (
    <ScreenShell refreshing={isLoading} onRefresh={load} scroll={false}>
      <View style={styles.header}>
        <Text style={styles.title}>Live Location</Text>
        <Text style={styles.subtitle}>
          {current ? `Updated ${formatTimestamp(current.timestamp)}` : "No data available"}
        </Text>
      </View>

      {error && (
        <Card>
          <Text style={styles.errorText}>{error}</Text>
        </Card>
      )}

      <View style={styles.mapWrap}>
        <LocationMap current={current} history={history} />
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  header: { padding: spacing.md, paddingBottom: 0 },
  title: { ...typography.h2, color: colors.textPrimary },
  subtitle: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.xs },
  mapWrap: { flex: 1, margin: spacing.md },
  emptyText: { ...typography.body, color: colors.textSecondary },
  errorText: { ...typography.body, color: colors.critical, margin: spacing.md },
});
