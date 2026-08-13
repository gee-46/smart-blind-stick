/**
 * Web implementation — deliberately does NOT import react-native-maps.
 *
 * Why: react-native-maps' native Fabric components get registered via
 * `codegenNativeComponent` from React Native's codegen pipeline. On web,
 * that import chain resolves into react-native-web's compatibility
 * layer, which does not implement a working `codegenNativeComponent`
 * for these native-only view managers -- so simply importing
 * react-native-maps at module-evaluation time on web throws:
 *
 *   TypeError: (0, _reactNativeWebDistIndex.codegenNativeComponent) is not a function
 *
 * react-native-maps has no supported web target at all (it's a native
 * bridge library), so there is no "make it work on web" fix here --
 * the only correct fix is to make sure web never evaluates that module.
 * Metro's platform-specific file resolution (`LocationMap.web.tsx` vs
 * `LocationMap.native.tsx`) does exactly that: this file is a fully
 * separate module graph from the native one, so react-native-maps
 * never appears in the web bundle.
 *
 * This renders the same real data (`current`, `history`) the native
 * map does -- just as a non-interactive readout instead of a map,
 * since there's no drop-in interactive map replacement here. No mock
 * GPS data, no hardcoded coordinates: if `current` is null, it shows
 * "No data available", exactly like the native version.
 */
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing, typography } from "../utils/theme";
import { formatTimestamp } from "../utils/format";
import { LocationHistoryItem, LocationPoint } from "../types/api";

interface LocationMapProps {
  current: LocationPoint | null;
  history: LocationHistoryItem[];
}

export function LocationMap({ current, history }: LocationMapProps) {
  if (!current) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>No data available</Text>
      </View>
    );
  }

  return (
    <View style={styles.container} accessibilityLabel="Smart Blind Stick's last known location (web fallback)">
      <View style={styles.badge}>
        <Text style={styles.badgeText}>📍 LAST KNOWN LOCATION</Text>
      </View>

      <View style={styles.coordRow}>
        <CoordBlock label="Latitude" value={current.latitude.toFixed(6)} />
        <CoordBlock label="Longitude" value={current.longitude.toFixed(6)} />
      </View>

      <View style={styles.statusRow}>
        <Text style={styles.statusLabel}>Status</Text>
        <Text style={styles.statusValue}>
          {current.fix_quality != null ? "GPS fix available" : "GPS status unknown"}
        </Text>
      </View>

      <Text style={styles.timestamp}>Updated {formatTimestamp(current.timestamp)}</Text>

      {history.length > 1 && (
        <Text style={styles.historyNote}>{history.length} location points recorded in history.</Text>
      )}

      <View style={styles.notice}>
        <Text style={styles.noticeText}>
          The interactive map is available in the Android and iOS app. This web view shows the same real backend
          data as a simple readout instead.
        </Text>
      </View>
    </View>
  );
}

function CoordBlock({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.coordBlock}>
      <Text style={styles.coordLabel}>{label}</Text>
      <Text style={styles.coordValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    minHeight: 320,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  badge: { alignSelf: "flex-start", marginBottom: spacing.md },
  badgeText: { ...typography.caption, color: colors.accent, fontWeight: "800", letterSpacing: 1 },
  coordRow: { flexDirection: "row", gap: spacing.lg, marginBottom: spacing.md },
  coordBlock: { flex: 1 },
  coordLabel: { ...typography.caption, color: colors.textSecondary },
  coordValue: { ...typography.h2, color: colors.textPrimary },
  statusRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: spacing.xs },
  statusLabel: { ...typography.body, color: colors.textSecondary },
  statusValue: { ...typography.bodyBold, color: colors.textPrimary },
  timestamp: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.md },
  historyNote: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.md },
  notice: {
    marginTop: "auto",
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  noticeText: { ...typography.caption, color: colors.textSecondary },
  empty: {
    minHeight: 200,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  emptyText: { ...typography.body, color: colors.textSecondary },
});
