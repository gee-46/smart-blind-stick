import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";

import * as deviceService from "../../services/deviceService";
import { useDevices } from "../../context/DeviceContext";
import { extractErrorMessage } from "../../services/api";
import { colors, minTouchTarget, radius, spacing, typography } from "../../utils/theme";

export default function PairingScreen() {
  const router = useRouter();
  const { refreshDevices, selectDevice } = useDevices();
  const [deviceId, setDeviceId] = useState("");
  const [nickname, setNickname] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = deviceId.trim().length > 0 && !isSubmitting;

  async function handlePair() {
    if (!canSubmit) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const paired = await deviceService.pairDevice(deviceId.trim(), nickname.trim() || undefined);
      await refreshDevices();
      selectDevice(paired.device_id);
      router.replace("/(app)/dashboard");
    } catch (err) {
      setError(
        extractErrorMessage(
          err,
          "Could not pair this device. Make sure the stick is powered on and has sent at least one check-in."
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Pair your Smart Blind Stick</Text>
      <Text style={styles.subtitle}>
        Enter the device ID printed on the stick, or shown in its setup screen. The stick must have already sent at
        least one status update to the backend.
      </Text>

      {error && (
        <View style={styles.errorBox} accessibilityLiveRegion="polite">
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <Text style={styles.label}>Device ID</Text>
      <TextInput
        value={deviceId}
        onChangeText={setDeviceId}
        placeholder="e.g. STICK_001"
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="characters"
        style={styles.input}
        accessibilityLabel="Device ID"
      />

      <Text style={styles.label}>Nickname (optional)</Text>
      <TextInput
        value={nickname}
        onChangeText={setNickname}
        placeholder="e.g. Dad's stick"
        placeholderTextColor={colors.textSecondary}
        style={styles.input}
        accessibilityLabel="Device nickname"
      />

      <Pressable
        onPress={handlePair}
        disabled={!canSubmit}
        accessibilityRole="button"
        style={({ pressed }) => [styles.button, (!canSubmit || pressed) && styles.buttonDisabled]}
      >
        {isSubmitting ? <ActivityIndicator color="#08131f" /> : <Text style={styles.buttonText}>Pair Device</Text>}
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, flexGrow: 1 },
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.xs },
  subtitle: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.lg },
  label: { ...typography.bodyBold, color: colors.textPrimary, marginBottom: spacing.xs, marginTop: spacing.sm },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    padding: spacing.md,
    color: colors.textPrimary,
    fontSize: 16,
    minHeight: minTouchTarget,
  },
  button: {
    backgroundColor: colors.accent,
    borderRadius: radius.md,
    minHeight: minTouchTarget,
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.lg,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { ...typography.h3, color: "#08131f" },
  errorBox: { backgroundColor: "rgba(224,32,58,0.15)", borderColor: colors.critical, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm, marginBottom: spacing.md },
  errorText: { ...typography.body, color: colors.critical },
});
