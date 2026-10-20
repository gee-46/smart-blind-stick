import React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "../utils/theme";

export default function SplashScreen() {
  return (
    <View style={styles.container} accessibilityLabel="Loading DrishtiGuard Guardian">
      <Text style={styles.title}>DrishtiGuard</Text>
      <Text style={styles.subtitle}>Guardian</Text>
      <ActivityIndicator size="large" color={colors.accent} style={{ marginTop: spacing.lg }} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, alignItems: "center", justifyContent: "center" },
  title: { ...typography.h1, color: colors.textPrimary },
  subtitle: { ...typography.h3, color: colors.accent, marginTop: spacing.xs },
});
