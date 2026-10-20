import React, { useEffect, useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { ScreenShell } from "../../components/ScreenShell";
import { Card } from "../../components/Card";
import { useAuth } from "../../context/AuthContext";
import { useDevices } from "../../context/DeviceContext";
import * as deviceService from "../../services/deviceService";
import * as notificationService from "../../services/notificationService";
import { colors, spacing, typography } from "../../utils/theme";

export default function SettingsScreen() {
  const router = useRouter();
  const { guardian, logout } = useAuth();
  const { devices, refreshDevices } = useDevices();
  const [pushStatus, setPushStatus] = useState<"idle" | "registering" | "registered" | "denied" | "error">("idle");

  useEffect(() => {
    registerPush();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function registerPush() {
    setPushStatus("registering");
    try {
      const token = await notificationService.registerForPushNotificationsAsync();
      if (!token) {
        setPushStatus("denied");
        return;
      }
      await notificationService.syncPushTokenWithBackend(token);
      setPushStatus("registered");
    } catch {
      setPushStatus("error");
    }
  }

  async function handleUnpair(deviceId: string) {
    Alert.alert("Unpair device?", `This removes ${deviceId} from your account.`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Unpair",
        style: "destructive",
        onPress: async () => {
          await deviceService.unpairDevice(deviceId);
          await refreshDevices();
        },
      },
    ]);
  }

  function handleLogout() {
    Alert.alert("Sign out?", "You can sign back in anytime.", [
      { text: "Cancel", style: "cancel" },
      { text: "Sign Out", style: "destructive", onPress: () => logout() },
    ]);
  }

  return (
    <ScreenShell>
      <Text style={styles.title}>Settings</Text>

      <Card>
        <Text style={styles.sectionTitle}>ACCOUNT</Text>
        <Text style={styles.value}>{guardian?.full_name}</Text>
        <Text style={styles.subvalue}>{guardian?.email}</Text>
        {guardian?.phone && <Text style={styles.subvalue}>{guardian.phone}</Text>}
      </Card>

      <Card>
        <View style={styles.rowBetween}>
          <Text style={styles.sectionTitle}>DEVICES</Text>
          <Pressable onPress={() => router.push("/(app)/pairing")} accessibilityRole="button">
            <Text style={styles.actionLink}>+ Pair new</Text>
          </Pressable>
        </View>
        {devices.length === 0 && <Text style={styles.subvalue}>No devices paired</Text>}
        {devices.map((device) => (
          <View key={device.device_id} style={styles.deviceRow}>
            <Text style={styles.value}>{device.nickname || device.device_id}</Text>
            <Pressable onPress={() => handleUnpair(device.device_id)} accessibilityRole="button">
              <Text style={styles.deleteLink}>Unpair</Text>
            </Pressable>
          </View>
        ))}
      </Card>

      <Card>
        <Text style={styles.sectionTitle}>NOTIFICATIONS</Text>
        <Text style={styles.subvalue}>
          {pushStatus === "registered" && "✅ Push notifications enabled"}
          {pushStatus === "registering" && "Registering…"}
          {pushStatus === "denied" && "⚠️ Permission denied — critical alerts may be missed"}
          {pushStatus === "error" && "⚠️ Could not register with the backend"}
          {pushStatus === "idle" && "Not yet registered"}
        </Text>
        {(pushStatus === "denied" || pushStatus === "error") && (
          <Pressable onPress={registerPush} accessibilityRole="button">
            <Text style={styles.actionLink}>Try again</Text>
          </Pressable>
        )}
      </Card>

      <Card>
        <Text style={styles.sectionTitle}>EMERGENCY CONTACTS</Text>
        <Pressable onPress={() => router.push("/(app)/contacts")} accessibilityRole="button">
          <Text style={styles.actionLink}>Manage emergency contacts</Text>
        </Pressable>
      </Card>

      <Card>
        <Text style={styles.sectionTitle}>PRIVACY</Text>
        <Text style={styles.subvalue}>
          Your location, device status, and event history are stored on your organization's own backend server, not
          a third-party cloud service.
        </Text>
      </Card>

      <Pressable onPress={handleLogout} accessibilityRole="button" style={styles.logoutButton}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </Pressable>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  sectionTitle: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.sm, letterSpacing: 1 },
  value: { ...typography.bodyBold, color: colors.textPrimary },
  subvalue: { ...typography.body, color: colors.textSecondary, marginTop: 2 },
  rowBetween: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.xs },
  deviceRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: spacing.xs },
  actionLink: { ...typography.body, color: colors.accent },
  deleteLink: { ...typography.body, color: colors.critical },
  logoutButton: {
    backgroundColor: colors.surface,
    borderColor: colors.critical,
    borderWidth: 1,
    borderRadius: 14,
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.md,
  },
  logoutText: { ...typography.h3, color: colors.critical },
});
