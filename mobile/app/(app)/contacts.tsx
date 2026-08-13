import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Switch, Text, TextInput, View } from "react-native";

import { ScreenShell } from "../../components/ScreenShell";
import { Card } from "../../components/Card";
import * as contactService from "../../services/contactService";
import { extractErrorMessage } from "../../services/api";
import { colors, minTouchTarget, radius, spacing, typography } from "../../utils/theme";
import { Contact } from "../../types/api";

export default function ContactsScreen() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [relationship, setRelationship] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setContacts(await contactService.listContacts());
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load emergency contacts."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAdd() {
    if (!name.trim() || !phone.trim()) return;
    setIsSaving(true);
    try {
      await contactService.addContact({
        name: name.trim(),
        phone: phone.trim(),
        relationship_label: relationship.trim() || undefined,
        is_primary: isPrimary,
      });
      setName("");
      setPhone("");
      setRelationship("");
      setIsPrimary(false);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not save this contact."));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await contactService.deleteContact(id);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not delete this contact."));
    }
  }

  async function handleSetPrimary(contact: Contact) {
    try {
      await contactService.updateContact(contact.id, {
        name: contact.name,
        phone: contact.phone,
        relationship_label: contact.relationship_label,
        is_primary: true,
      });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not update this contact."));
    }
  }

  return (
    <ScreenShell refreshing={isLoading} onRefresh={load}>
      <Text style={styles.title}>Emergency Contacts</Text>
      {error && <Text style={styles.errorText}>{error}</Text>}

      {contacts.length === 0 && !isLoading && (
        <Card>
          <Text style={styles.emptyText}>No data available</Text>
        </Card>
      )}

      {contacts.map((contact) => (
        <Card key={contact.id}>
          <View style={styles.contactRow}>
            <View style={styles.contactInfo}>
              <Text style={styles.contactName}>
                {contact.name} {contact.is_primary ? "⭐" : ""}
              </Text>
              <Text style={styles.contactDetail}>{contact.phone}</Text>
              {contact.relationship_label && <Text style={styles.contactDetail}>{contact.relationship_label}</Text>}
            </View>
            <View style={styles.contactActions}>
              {!contact.is_primary && (
                <Pressable onPress={() => handleSetPrimary(contact)} accessibilityRole="button">
                  <Text style={styles.actionLink}>Set primary</Text>
                </Pressable>
              )}
              <Pressable onPress={() => handleDelete(contact.id)} accessibilityRole="button">
                <Text style={styles.deleteLink}>Delete</Text>
              </Pressable>
            </View>
          </View>
        </Card>
      ))}

      <Card>
        <Text style={styles.sectionTitle}>ADD CONTACT</Text>
        <TextInput
          value={name}
          onChangeText={setName}
          placeholder="Name"
          placeholderTextColor={colors.textSecondary}
          style={styles.input}
          accessibilityLabel="Contact name"
        />
        <TextInput
          value={phone}
          onChangeText={setPhone}
          placeholder="Phone number"
          placeholderTextColor={colors.textSecondary}
          style={styles.input}
          keyboardType="phone-pad"
          accessibilityLabel="Contact phone number"
        />
        <TextInput
          value={relationship}
          onChangeText={setRelationship}
          placeholder="Relationship (optional)"
          placeholderTextColor={colors.textSecondary}
          style={styles.input}
          accessibilityLabel="Relationship"
        />
        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Set as primary contact</Text>
          <Switch value={isPrimary} onValueChange={setIsPrimary} accessibilityLabel="Set as primary contact" />
        </View>
        <Pressable
          onPress={handleAdd}
          disabled={isSaving || !name.trim() || !phone.trim()}
          accessibilityRole="button"
          style={[styles.button, (isSaving || !name.trim() || !phone.trim()) && styles.buttonDisabled]}
        >
          {isSaving ? <ActivityIndicator color="#08131f" /> : <Text style={styles.buttonText}>Add Contact</Text>}
        </Pressable>
      </Card>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  sectionTitle: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.sm, letterSpacing: 1 },
  emptyText: { ...typography.body, color: colors.textSecondary },
  errorText: { ...typography.body, color: colors.critical, marginBottom: spacing.sm },
  contactRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  contactInfo: { flexShrink: 1 },
  contactName: { ...typography.bodyBold, color: colors.textPrimary },
  contactDetail: { ...typography.caption, color: colors.textSecondary },
  contactActions: { alignItems: "flex-end", gap: spacing.xs },
  actionLink: { ...typography.caption, color: colors.accent },
  deleteLink: { ...typography.caption, color: colors.critical },
  input: {
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    padding: spacing.md,
    color: colors.textPrimary,
    fontSize: 16,
    minHeight: minTouchTarget,
    marginBottom: spacing.sm,
  },
  switchRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md },
  switchLabel: { ...typography.body, color: colors.textPrimary },
  button: {
    backgroundColor: colors.accent,
    borderRadius: radius.md,
    minHeight: minTouchTarget,
    alignItems: "center",
    justifyContent: "center",
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { ...typography.h3, color: "#08131f" },
});
