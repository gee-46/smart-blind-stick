import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Card } from "./Card";
import { colors, riskColor, spacing, typography } from "../utils/theme";
import { formatTimestamp } from "../utils/format";
import { EventOut } from "../types/api";

const SOURCE_LABEL: Record<string, string> = {
  ai_vision: "AI VISION",
  sensor_fusion: "SENSOR",
  safety_engine: "SAFETY ENGINE",
  manual: "MANUAL",
};

export function EventCard({ event }: { event: EventOut }) {
  const extra = (event.extra ?? {}) as Record<string, unknown>;
  const color = event.risk_level ? riskColor[event.risk_level] ?? colors.accent : colors.accent;

  return (
    <Card accessibilityLabel={`${event.event_type} event, ${event.message ?? ""}`}>
      <View style={styles.headerRow}>
        <Text style={styles.sourceTag}>{SOURCE_LABEL[event.source] ?? event.source.toUpperCase()}</Text>
        <Text style={styles.timestamp}>{formatTimestamp(event.timestamp)}</Text>
      </View>

      <Text style={[styles.eventType, { color }]}>{event.event_type.replace(/_/g, " ").toUpperCase()}</Text>

      {event.message && <Text style={styles.message}>{event.message}</Text>}

      <View style={styles.detailsGrid}>
        {typeof extra.object === "string" && <Detail label="Object" value={String(extra.object)} />}
        {typeof extra.direction === "string" && <Detail label="Direction" value={String(extra.direction).toUpperCase()} />}
        {typeof extra.distance_m === "number" && <Detail label="Distance" value={`${extra.distance_m} m`} />}
        {typeof extra.movement === "string" && <Detail label="Movement" value={String(extra.movement).toUpperCase()} />}
        {typeof extra.confidence === "number" && (
          <Detail label="Confidence" value={`${Math.round(Number(extra.confidence) * 100)}%`} />
        )}
        {typeof extra.level === "string" && <Detail label="Level" value={String(extra.level).toUpperCase()} />}
      </View>
    </Card>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detailItem}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: spacing.xs },
  sourceTag: { ...typography.caption, color: colors.accent, fontWeight: "800", letterSpacing: 0.5 },
  timestamp: { ...typography.caption, color: colors.textSecondary },
  eventType: { ...typography.h3, marginBottom: spacing.xs },
  message: { ...typography.body, color: colors.textPrimary, marginBottom: spacing.sm },
  detailsGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  detailItem: { minWidth: 90 },
  detailLabel: { ...typography.caption, color: colors.textSecondary },
  detailValue: { ...typography.bodyBold, color: colors.textPrimary },
});
