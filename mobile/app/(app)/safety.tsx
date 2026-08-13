import React, { useCallback, useEffect, useState } from "react";
import { StyleSheet, Text } from "react-native";

import { ScreenShell } from "../../components/ScreenShell";
import { Card } from "../../components/Card";
import { SafetyCard } from "../../components/SafetyCard";
import { EventCard } from "../../components/EventCard";
import { useDevices } from "../../context/DeviceContext";
import { useDeviceSocket } from "../../hooks/useDeviceSocket";
import * as eventService from "../../services/eventService";
import { extractErrorMessage } from "../../services/api";
import { colors, spacing, typography } from "../../utils/theme";
import { EventOut, WSMessage } from "../../types/api";

export default function SafetyScreen() {
  const { selectedDevice } = useDevices();
  const [latest, setLatest] = useState<EventOut | null>(null);
  const [recent, setRecent] = useState<EventOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!selectedDevice) return;
    setIsLoading(true);
    setError(null);
    try {
      const events = await eventService.getEvents(selectedDevice.device_id, { limit: 100 });
      const safetyEvents = events.filter((event) => event.source === "safety_engine" || event.risk_level);
      setRecent(safetyEvents.slice(0, 20));
      setLatest(safetyEvents[0] ?? null);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load safety events."));
    } finally {
      setIsLoading(false);
    }
  }, [selectedDevice]);

  useEffect(() => {
    load();
  }, [load]);

  const handleWsMessage = useCallback(
    (message: WSMessage) => {
      if (message.type === "safety_update" && selectedDevice) {
        const event: EventOut = {
          id: 0,
          device_id: selectedDevice.device_id,
          source: "safety_engine",
          event_type: "safety_update",
          risk_level: message.risk_level as EventOut["risk_level"],
          message: (message.message as string) ?? null,
          extra: null,
          timestamp: message.timestamp as string,
        };
        setLatest(event);
        setRecent((prev) => [event, ...prev].slice(0, 20));
      }
    },
    [selectedDevice]
  );

  useDeviceSocket(selectedDevice?.device_id ?? null, handleWsMessage);

  if (!selectedDevice) {
    return (
      <ScreenShell>
        <Card>
          <Text style={styles.emptyText}>Pair a device first to see safety status.</Text>
        </Card>
      </ScreenShell>
    );
  }

  return (
    <ScreenShell refreshing={isLoading} onRefresh={load}>
      <Text style={styles.title}>Safety</Text>
      <SafetyCard event={latest} />

      <Text style={styles.sectionTitle}>RECENT SAFETY EVENTS</Text>
      {error && <Text style={styles.errorText}>{error}</Text>}
      {recent.length === 0 && !error && <Text style={styles.emptyText}>No events recorded</Text>}
      {recent.map((event, idx) => (
        <EventCard key={event.id || idx} event={event} />
      ))}
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  sectionTitle: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.md, marginBottom: spacing.sm, letterSpacing: 1 },
  emptyText: { ...typography.body, color: colors.textSecondary },
  errorText: { ...typography.body, color: colors.critical, marginBottom: spacing.sm },
});
