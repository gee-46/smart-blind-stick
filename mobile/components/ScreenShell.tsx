import React from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";

import { BottomNav } from "./BottomNav";
import { colors, spacing } from "../utils/theme";

interface ScreenShellProps {
  children: React.ReactNode;
  showNav?: boolean;
  refreshing?: boolean;
  onRefresh?: () => void;
  scroll?: boolean;
}

export function ScreenShell({ children, showNav = true, refreshing, onRefresh, scroll = true }: ScreenShellProps) {
  const content = scroll ? (
    <ScrollView
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        onRefresh ? <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh} tintColor={colors.accent} /> : undefined
      }
    >
      {children}
    </ScrollView>
  ) : (
    <View style={styles.flexContent}>{children}</View>
  );

  return (
    <View style={styles.container}>
      {content}
      {showNav && <BottomNav />}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scrollContent: { padding: spacing.md, paddingBottom: spacing.xl },
  flexContent: { flex: 1, padding: spacing.md },
});
