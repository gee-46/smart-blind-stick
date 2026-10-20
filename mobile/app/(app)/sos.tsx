import React, { useCallback, useState } from "react";
import { Alert, StyleSheet, Text } from "react-native";

import { ScreenShell } from "../../components/ScreenShell";
import { Card } from "../../components/Card";
import { SOSCard } from "../../components/SOSCard";
import { EventCard } from "../../components/EventCard";
import { useDevices } from "../../context/DeviceContext";
import { useDeviceSocket } from "../../hooks/useDeviceSocket";
import * as sosService from "../../services/sosService";
import { extractErrorMessage } from "../../services/api";
import { colors, spacing, typography } from "../../utils/theme";
import { EventOut, WSMessage } from "../../types/api";

interface ActiveSOS {
  reason?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  timestamp?: string | null;
}

export default function SOSScreen() {
  const { selectedDevice } = useDevices();
  const [active, setActive] = useState<ActiveSOS | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [recentCritical, setRecentCritical] = useState<EventOut[]>([]);

  const handleWsMessage = useCallback((message: WSMessage) => {
    if (message.type === "sos") {
      setActive({
        reason: message.reason as string,
        latitude: message.latitude as number,
        longitude: message.longitude as number,
        timestamp: message.timestamp as string,
      });
    }
  }, []);

  useDeviceSocket(selectedDevice?.device_id ?? null, handleWsMessage);

  const loadHistory = useCallback(async () => {
    if (!selectedDevice) return;
    try {
      const events = await sosService.getRecentCriticalEvents(selectedDevice.device_id);
      setRecentCritical(events);
    } catch {
      // Non-fatal -- the live SOS card still works without history.
    }
  }, [selectedDevice]);

  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function handleTrigger() {
    if (!selectedDevice) return;

    Alert.alert(
      "Trigger Emergency SOS?",
      "This sends a real emergency alert through the backend, exactly as if the stick triggered it.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Trigger SOS",
          style: "destructive",
          onPress: async () => {
            setIsTriggering(true);
            try {
              await sosService.triggerSOS({ device_id: selectedDevice.device_id, reason: "guardian_triggered" });
              setActive({ reason: "guardian_triggered", timestamp: new Date().toISOString() });
            } catch (err) {
              Alert.alert("SOS failed", extractErrorMessage(err, "Could not reach the backend to trigger SOS."));
            } finally {
              setIsTriggering(false);
            }
          },
        },
      ]
    );
  }

  if (!selectedDevice) {
    return (
      <ScreenShell>
        <Card>
          <Text style={styles.emptyText}>Pair a device first to use emergency SOS.</Text>
        </Card>
      </ScreenShell>
    );
  }

  return (
    <ScreenShell onRefresh={loadHistory}>
      <Text style={styles.title}>Emergency SOS</Text>

      <SOSCard
        active={!!active}
        reason={active?.reason}
        latitude={active?.latitude}
        longitude={active?.longitude}
        timestamp={active?.timestamp}
        onTrigger={handleTrigger}
        isTriggering={isTriggering}
      />

      <Text style={styles.sectionTitle}>RECENT CRITICAL EVENTS</Text>
      {recentCritical.length === 0 && <Text style={styles.emptyText}>No events recorded</Text>}
      {recentCritical.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  sectionTitle: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.md, marginBottom: spacing.sm, letterSpacing: 1 },
  emptyText: { ...typography.body, color: colors.textSecondary },
});
