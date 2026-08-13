import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Card } from "./Card";
import { colors, riskColor, riskLabel, spacing, typography } from "../utils/theme";
import { formatTimestamp } from "../utils/format";
import { EventOut } from "../types/api";

/**
 * Displays the Safety Engine's final risk level for the most recent
 * relevant event. This component never computes risk itself -- it only
 * renders `event.risk_level` and `event.message` exactly as the backend
 * reported them, per spec section 15.
 */
export function SafetyCard({ event }: { event: EventOut | null }) {
  if (!event || !event.risk_level) {
    return (
      <Card>
        <Text style={styles.heading}>SAFETY</Text>
        <Text style={styles.emptyText}>No data available</Text>
      </Card>
    );
  }

  const color = riskColor[event.risk_level] ?? colors.textSecondary;
  const label = riskLabel[event.risk_level] ?? event.risk_level.toUpperCase();
  const extra = (event.extra ?? {}) as Record<string, unknown>;

  return (
    <Card accessibilityLabel={`Safety status: ${label}. ${event.message ?? ""}`}>
      <Text style={styles.heading}>SAFETY</Text>
      <View style={[styles.badge, { backgroundColor: color }]}>
        <Text style={styles.badgeText}>{label}</Text>
      </View>
      {event.message && <Text style={styles.message}>{event.message}</Text>}
      <View style={styles.metaRow}>
        {typeof extra.distance_m === "number" && (
          <Text style={styles.meta}>Distance: {extra.distance_m} m</Text>
        )}
        <Text style={styles.meta}>{formatTimestamp(event.timestamp)}</Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  heading: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.xs, letterSpacing: 1 },
  badge: { alignSelf: "flex-start", paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: 999, marginBottom: spacing.sm },
  badgeText: { ...typography.bodyBold, color: "#08131f" },
  message: { ...typography.body, color: colors.textPrimary, marginBottom: spacing.xs },
  metaRow: { flexDirection: "row", justifyContent: "space-between" },
  meta: { ...typography.caption, color: colors.textSecondary },
  emptyText: { ...typography.body, color: colors.textSecondary },
});
