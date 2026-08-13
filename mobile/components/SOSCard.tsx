import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { Card } from "./Card";
import { colors, minTouchTarget, spacing, typography } from "../utils/theme";
import { formatTimestamp } from "../utils/format";

interface SOSCardProps {
  active: boolean;
  reason?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  timestamp?: string | null;
  onTrigger: () => void;
  isTriggering: boolean;
}

export function SOSCard({ active, reason, latitude, longitude, timestamp, onTrigger, isTriggering }: SOSCardProps) {
  return (
    <Card style={active ? styles.activeCard : undefined} accessibilityLabel={active ? "SOS active" : "No active SOS"}>
      <Text style={styles.heading}>EMERGENCY</Text>

      {active ? (
        <View>
          <Text style={styles.activeLabel}>🆘 SOS ACTIVE</Text>
          {reason && <Text style={styles.detail}>Reason: {reason}</Text>}
          {latitude != null && longitude != null && (
            <Text style={styles.detail}>
              Location: {latitude.toFixed(5)}, {longitude.toFixed(5)}
            </Text>
          )}
          {timestamp && <Text style={styles.detail}>Time: {formatTimestamp(timestamp)}</Text>}
        </View>
      ) : (
        <Text style={styles.idleLabel}>No active SOS</Text>
      )}

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Trigger emergency SOS"
        onPress={onTrigger}
        disabled={isTriggering}
        style={({ pressed }) => [styles.sosButton, pressed && styles.sosButtonPressed]}
      >
        {isTriggering ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.sosButtonText}>TRIGGER SOS</Text>
        )}
      </Pressable>
    </Card>
  );
}

const styles = StyleSheet.create({
  activeCard: { borderColor: colors.critical, borderWidth: 2 },
  heading: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.sm, letterSpacing: 1 },
  activeLabel: { ...typography.h2, color: colors.critical, marginBottom: spacing.xs },
  idleLabel: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.md },
  detail: { ...typography.body, color: colors.textPrimary },
  sosButton: {
    marginTop: spacing.md,
    backgroundColor: colors.critical,
    borderRadius: 14,
    minHeight: minTouchTarget,
    alignItems: "center",
    justifyContent: "center",
  },
  sosButtonPressed: { opacity: 0.8 },
  sosButtonText: { ...typography.h3, color: "#fff", letterSpacing: 1 },
});
