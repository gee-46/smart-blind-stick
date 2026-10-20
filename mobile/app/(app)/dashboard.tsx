import React, { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { ScreenShell } from "../../components/ScreenShell";
import { Card } from "../../components/Card";
import { DeviceStatusCard } from "../../components/DeviceStatusCard";
import { BatteryCard } from "../../components/BatteryCard";
import { SafetyCard } from "../../components/SafetyCard";
import { useAuth } from "../../context/AuthContext";
import { useDevices } from "../../context/DeviceContext";
import { useDeviceSocket } from "../../hooks/useDeviceSocket";
import * as eventService from "../../services/eventService";
import { colors, spacing, typography } from "../../utils/theme";
import { EventOut, WSMessage } from "../../types/api";
import {
  describeEventForNotification,
  isCriticalWSEvent,
  presentCriticalAlert,
} from "../../services/notificationService";

export default function DashboardScreen() {
  const router = useRouter();
  const { guardian } = useAuth();
  const { devices, selectedDevice, isLoading, error, refreshDevices, applyLiveUpdate } = useDevices();
  const [latestSafetyEvent, setLatestSafetyEvent] = useState<EventOut | null>(null);
  const [latestAiEvent, setLatestAiEvent] = useState<EventOut | null>(null);
  const [sosActive, setSosActive] = useState<{ reason?: string; timestamp?: string } | null>(null);

  const loadLatestEvents = useCallback(async (deviceId: string) => {
    const [safety, ai] = await Promise.all([
      eventService.getLatestEvent(deviceId, "safety_engine").catch(() => null),
      eventService.getLatestEvent(deviceId, "ai_vision").catch(() => null),
    ]);
    setLatestSafetyEvent(safety);
    setLatestAiEvent(ai);
  }, []);

  useEffect(() => {
    if (selectedDevice) {
      loadLatestEvents(selectedDevice.device_id);
    }
  }, [selectedDevice, loadLatestEvents]);

  const handleWsMessage = useCallback(
    (message: WSMessage) => {
      if (!selectedDevice) return;

      if (message.type === "battery_update" && typeof message.battery === "number") {
        applyLiveUpdate(selectedDevice.device_id, { battery: message.battery });
      }
      if (message.type === "device_online") {
        applyLiveUpdate(selectedDevice.device_id, { online: true });
      }
      if (message.type === "device_offline") {
        applyLiveUpdate(selectedDevice.device_id, { online: false, last_seen: message.last_seen as string });
      }
      if (message.type === "location_update") {
        applyLiveUpdate(selectedDevice.device_id, { last_seen: message.timestamp as string, online: true });
      }
      if (message.type === "safety_update") {
        setLatestSafetyEvent((prev) => ({
          ...(prev ?? ({} as EventOut)),
          risk_level: message.risk_level as EventOut["risk_level"],
          message: message.message as string,
          timestamp: message.timestamp as string,
          source: "safety_engine",
          event_type: "safety_update",
          device_id: selectedDevice.device_id,
          extra: prev?.extra ?? null,
          id: prev?.id ?? 0,
        }));
      }
      if (message.type === "object_detected" || message.type === "obstacle" || message.type === "danger") {
        setLatestAiEvent({
          id: 0,
          device_id: selectedDevice.device_id,
          source: (message.source as string) ?? "ai_vision",
          event_type: message.type,
          risk_level: (message.risk_level as EventOut["risk_level"]) ?? null,
          message: (message.message as string) ?? null,
          extra: (message.extra as Record<string, unknown>) ?? null,
          timestamp: message.timestamp as string,
        });
      }
      if (message.type === "sos") {
        setSosActive({ reason: message.reason as string, timestamp: message.timestamp as string });
      }

      if (isCriticalWSEvent({ type: message.type, risk_level: message.risk_level as string | undefined })) {
        const { title, body } = describeEventForNotification(message as { type: string; message?: unknown });
        presentCriticalAlert(title, body);
      }
    },
    [selectedDevice, applyLiveUpdate]
  );

  const { status: wsStatus } = useDeviceSocket(selectedDevice?.device_id ?? null, handleWsMessage);

  if (!isLoading && devices.length === 0) {
    return (
      <ScreenShell>
        <Text style={styles.greeting}>Hi{guardian ? `, ${guardian.full_name.split(" ")[0]}` : ""} 👋</Text>
        <Card>
          <Text style={styles.emptyTitle}>No device paired yet</Text>
          <Text style={styles.emptyBody}>Pair your Smart Blind Stick to start monitoring.</Text>
          <Pressable
            accessibilityRole="button"
            style={styles.pairButton}
            onPress={() => router.push("/(app)/pairing")}
          >
            <Text style={styles.pairButtonText}>Pair a Device</Text>
          </Pressable>
        </Card>
      </ScreenShell>
    );
  }

  return (
    <ScreenShell refreshing={isLoading} onRefresh={refreshDevices}>
      <Text style={styles.greeting}>Hi{guardian ? `, ${guardian.full_name.split(" ")[0]}` : ""} 👋</Text>

      <View style={styles.connectionRow}>
        <View style={[styles.dot, { backgroundColor: wsStatus === "open" ? colors.online : colors.offline }]} />
        <Text style={styles.connectionText}>
          {wsStatus === "open" ? "Live updates connected" : wsStatus === "connecting" ? "Connecting…" : "Live updates offline"}
        </Text>
      </View>

      {error && (
        <Card>
          <Text style={styles.errorText}>{error}</Text>
        </Card>
      )}

      {selectedDevice && (
        <>
          <DeviceStatusCard device={selectedDevice} />
          {sosActive && (
            <Card style={styles.sosBanner}>
              <Text style={styles.sosBannerText}>🆘 SOS ACTIVE — tap Emergency to view details</Text>
              <Pressable onPress={() => router.push("/(app)/sos")} accessibilityRole="button">
                <Text style={styles.sosBannerLink}>View SOS</Text>
              </Pressable>
            </Card>
          )}
          <SafetyCard event={latestSafetyEvent} />
          <BatteryCard battery={selectedDevice.battery} />

          <Card>
            <Text style={styles.sectionTitle}>LATEST AI VISION EVENT</Text>
            {latestAiEvent ? (
              <>
                <Text style={styles.eventTitle}>{latestAiEvent.event_type.replace(/_/g, " ").toUpperCase()}</Text>
                {latestAiEvent.message && <Text style={styles.eventMessage}>{latestAiEvent.message}</Text>}
              </>
            ) : (
              <Text style={styles.emptyBody}>No events recorded</Text>
            )}
          </Card>
        </>
      )}
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  greeting: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.sm },
  connectionRow: { flexDirection: "row", alignItems: "center", marginBottom: spacing.md, gap: spacing.xs },
  dot: { width: 8, height: 8, borderRadius: 4 },
  connectionText: { ...typography.caption, color: colors.textSecondary },
  emptyTitle: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.xs },
  emptyBody: { ...typography.body, color: colors.textSecondary },
  pairButton: {
    marginTop: spacing.md,
    backgroundColor: colors.accent,
    borderRadius: 14,
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
  },
  pairButtonText: { ...typography.h3, color: "#08131f" },
  sectionTitle: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.xs, letterSpacing: 1 },
  eventTitle: { ...typography.h3, color: colors.textPrimary },
  eventMessage: { ...typography.body, color: colors.textSecondary, marginTop: spacing.xs },
  errorText: { ...typography.body, color: colors.critical },
  sosBanner: { backgroundColor: colors.critical, borderColor: colors.critical },
  sosBannerText: { ...typography.bodyBold, color: "#fff" },
  sosBannerLink: { ...typography.body, color: "#fff", textDecorationLine: "underline", marginTop: spacing.xs },
});
