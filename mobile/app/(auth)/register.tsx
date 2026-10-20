import React, { useState } from "react";
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { Link } from "expo-router";

import { useAuth } from "../../context/AuthContext";
import { extractErrorMessage } from "../../services/api";
import { colors, minTouchTarget, radius, spacing, typography } from "../../utils/theme";

export default function RegisterScreen() {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = fullName.trim().length > 0 && email.trim().length > 0 && password.length >= 8 && !isSubmitting;

  async function handleSubmit() {
    if (!canSubmit) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await register({
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim(),
        phone: phone.trim() || undefined,
      });
    } catch (err) {
      setError(extractErrorMessage(err, "Registration failed. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.flex}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Create your account</Text>
        <Text style={styles.subtitle}>Your Guardian account is stored securely in the backend</Text>

        {error && (
          <View style={styles.errorBox} accessibilityLiveRegion="polite">
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        <Text style={styles.label}>Full name</Text>
        <TextInput value={fullName} onChangeText={setFullName} style={styles.input} accessibilityLabel="Full name" placeholder="Asha Rao" placeholderTextColor={colors.textSecondary} />

        <Text style={styles.label}>Email</Text>
        <TextInput
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          accessibilityLabel="Email address"
          placeholder="you@example.com"
          placeholderTextColor={colors.textSecondary}
          autoCapitalize="none"
          keyboardType="email-address"
        />

        <Text style={styles.label}>Phone (optional)</Text>
        <TextInput value={phone} onChangeText={setPhone} style={styles.input} accessibilityLabel="Phone number" placeholder="+91 90000 00000" placeholderTextColor={colors.textSecondary} keyboardType="phone-pad" />

        <Text style={styles.label}>Password (min 8 characters)</Text>
        <TextInput value={password} onChangeText={setPassword} style={styles.input} accessibilityLabel="Password" secureTextEntry placeholder="••••••••" placeholderTextColor={colors.textSecondary} />

        <Pressable
          onPress={handleSubmit}
          disabled={!canSubmit}
          accessibilityRole="button"
          style={({ pressed }) => [styles.button, (!canSubmit || pressed) && styles.buttonDisabled]}
        >
          {isSubmitting ? <ActivityIndicator color="#08131f" /> : <Text style={styles.buttonText}>Create Account</Text>}
        </Pressable>

        <Link href="/(auth)/login" asChild>
          <Pressable accessibilityRole="link" style={styles.linkButton}>
            <Text style={styles.linkText}>Already have an account? Sign in</Text>
          </Pressable>
        </Link>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { padding: spacing.lg, flexGrow: 1, justifyContent: "center" },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.xs },
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
  linkButton: { marginTop: spacing.lg, alignItems: "center", minHeight: minTouchTarget, justifyContent: "center" },
  linkText: { ...typography.body, color: colors.accent },
  errorBox: { backgroundColor: "rgba(224,32,58,0.15)", borderColor: colors.critical, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm, marginBottom: spacing.md },
  errorText: { ...typography.body, color: colors.critical },
});
