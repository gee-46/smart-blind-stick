import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Card } from "./Card";
import { colors, spacing, typography } from "../utils/theme";
import { formatRelativeTime } from "../utils/format";
import { PairedDevice } from "../types/api";

export function DeviceStatusCard({ device }: { device: PairedDevice }) {
  const isOnline = device.online;

  return (
    <Card accessibilityRole="summary" accessibilityLabel={`Device ${device.nickname ?? device.device_id}, ${isOnline ? "online" : "offline"}`}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>{device.nickname || device.device_id}</Text>
        <View style={[styles.statusPill, { backgroundColor: isOnline ? colors.online : colors.offline }]}>
          <Text style={styles.statusPillText}>{isOnline ? "🟢 ONLINE" : "⚪ OFFLINE"}</Text>
        </View>
      </View>

      <Text style={styles.deviceId}>ID: {device.device_id}</Text>

      <View style={styles.row}>
        <StatRow label="Last seen" value={formatRelativeTime(device.last_seen)} />
        <StatRow label="GPS" value={device.gps_available ? "Available" : "Unavailable"} />
      </View>

      {!isOnline && (
        <Text style={styles.offlineNote}>
          The stick has not checked in recently. Showing last known information.
        </Text>
      )}
    </Card>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.xs },
  title: { ...typography.h3, color: colors.textPrimary, flexShrink: 1 },
  deviceId: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.sm },
  statusPill: { paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: 999 },
  statusPillText: { ...typography.caption, color: "#08131f", fontWeight: "800" },
  row: { flexDirection: "row", gap: spacing.lg },
  stat: { marginRight: spacing.lg },
  statLabel: { ...typography.caption, color: colors.textSecondary },
  statValue: { ...typography.bodyBold, color: colors.textPrimary },
  offlineNote: { ...typography.caption, color: colors.medium, marginTop: spacing.sm },
});
