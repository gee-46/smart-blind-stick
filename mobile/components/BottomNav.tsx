import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter, useSegments } from "expo-router";

import { colors, minTouchTarget, spacing, typography } from "../utils/theme";

const TABS: { key: string; label: string; icon: string; href: string }[] = [
  { key: "dashboard", label: "Dashboard", icon: "🏠", href: "/(app)/dashboard" },
  { key: "location", label: "Location", icon: "📍", href: "/(app)/location" },
  { key: "events", label: "Events", icon: "📋", href: "/(app)/events" },
  { key: "sos", label: "SOS", icon: "🆘", href: "/(app)/sos" },
  { key: "settings", label: "Settings", icon: "⚙️", href: "/(app)/settings" },
];

export function BottomNav() {
  const router = useRouter();
  const segments = useSegments();
  const active = segments[segments.length - 1];

  return (
    <View style={styles.bar} accessibilityRole="tablist">
      {TABS.map((tab) => {
        const isActive = active === tab.key;
        return (
          <Pressable
            key={tab.key}
            onPress={() => router.push(tab.href as never)}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
            accessibilityLabel={tab.label}
            style={styles.tab}
          >
            <Text style={styles.icon}>{tab.icon}</Text>
            <Text style={[styles.label, isActive && styles.labelActive]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: "row",
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
    paddingVertical: spacing.xs,
  },
  tab: { flex: 1, alignItems: "center", justifyContent: "center", minHeight: minTouchTarget, gap: 2 },
  icon: { fontSize: 20 },
  label: { ...typography.caption, color: colors.textSecondary },
  labelActive: { color: colors.accent, fontWeight: "800" },
});
