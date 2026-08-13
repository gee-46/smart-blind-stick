import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Card } from "./Card";
import { colors, spacing, typography } from "../utils/theme";
import { batteryLabel } from "../utils/format";

const LEVEL_COLOR: Record<string, string> = {
  good: colors.safe,
  normal: colors.low,
  low: colors.medium,
  critical: colors.critical,
  unknown: colors.offline,
};

export function BatteryCard({ battery }: { battery: number | null }) {
  const { label, level } = batteryLabel(battery);
  const displayValue = battery === null || battery === undefined ? "No data available" : `${battery}%`;

  return (
    <Card accessibilityLabel={`Battery ${displayValue}, ${label}`}>
      <Text style={styles.heading}>BATTERY</Text>
      <View style={styles.row}>
        <Text style={styles.value}>{displayValue}</Text>
        <View style={[styles.pill, { backgroundColor: LEVEL_COLOR[level] }]}>
          <Text style={styles.pillText}>{label.toUpperCase()}</Text>
        </View>
      </View>
      {battery !== null && battery !== undefined && (
        <View style={styles.track}>
          <View style={[styles.fill, { width: `${Math.max(4, battery)}%`, backgroundColor: LEVEL_COLOR[level] }]} />
        </View>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  heading: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.xs, letterSpacing: 1 },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  value: { ...typography.h2, color: colors.textPrimary },
  pill: { paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: 999 },
  pillText: { ...typography.caption, color: "#08131f", fontWeight: "800" },
  track: { height: 10, borderRadius: 6, backgroundColor: colors.surfaceElevated, marginTop: spacing.sm, overflow: "hidden" },
  fill: { height: "100%", borderRadius: 6 },
});
