import React, { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { ScreenShell } from "../../components/ScreenShell";
import { Card } from "../../components/Card";
import { EventCard } from "../../components/EventCard";
import { useDevices } from "../../context/DeviceContext";
import * as eventService from "../../services/eventService";
import { extractErrorMessage } from "../../services/api";
import { colors, spacing, typography } from "../../utils/theme";
import { EventOut } from "../../types/api";

const RISK_FILTERS = ["all", "critical", "high", "medium", "low", "safe"] as const;
const SOURCE_FILTERS = ["all", "ai_vision", "sensor_fusion", "safety_engine"] as const;

export default function EventsScreen() {
  const { selectedDevice } = useDevices();
  const [events, setEvents] = useState<EventOut[]>([]);
  const [riskFilter, setRiskFilter] = useState<(typeof RISK_FILTERS)[number]>("all");
  const [sourceFilter, setSourceFilter] = useState<(typeof SOURCE_FILTERS)[number]>("all");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!selectedDevice) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await eventService.getEvents(selectedDevice.device_id, {
        limit: 200,
        risk_level: riskFilter === "all" ? undefined : riskFilter,
      });
      setEvents(result);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load event history."));
    } finally {
      setIsLoading(false);
    }
  }, [selectedDevice, riskFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = events.filter((event) => sourceFilter === "all" || event.source === sourceFilter);

  if (!selectedDevice) {
    return (
      <ScreenShell>
        <Card>
          <Text style={styles.emptyText}>Pair a device first to see its event history.</Text>
        </Card>
      </ScreenShell>
    );
  }

  return (
    <ScreenShell refreshing={isLoading} onRefresh={load}>
      <Text style={styles.title}>Event History</Text>

      <FilterRow label="Risk" options={RISK_FILTERS} value={riskFilter} onChange={setRiskFilter} />
      <FilterRow label="Source" options={SOURCE_FILTERS} value={sourceFilter} onChange={setSourceFilter} />

      {error && (
        <Card>
          <Text style={styles.errorText}>{error}</Text>
        </Card>
      )}

      {filtered.length === 0 && !error && (
        <Card>
          <Text style={styles.emptyText}>No events recorded</Text>
        </Card>
      )}

      {filtered.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </ScreenShell>
  );
}

function FilterRow<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <View style={styles.filterBlock}>
      <Text style={styles.filterLabel}>{label}</Text>
      <View style={styles.filterRow}>
        {options.map((option) => {
          const active = option === value;
          return (
            <Pressable
              key={option}
              onPress={() => onChange(option)}
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
              style={[styles.chip, active && styles.chipActive]}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>
                {option === "all" ? "All" : option.replace(/_/g, " ")}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  title: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  filterBlock: { marginBottom: spacing.md },
  filterLabel: { ...typography.caption, color: colors.textSecondary, marginBottom: spacing.xs },
  filterRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  chip: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    minHeight: 36,
    justifyContent: "center",
  },
  chipActive: { backgroundColor: colors.accent, borderColor: colors.accent },
  chipText: { ...typography.caption, color: colors.textSecondary, textTransform: "capitalize" },
  chipTextActive: { color: "#08131f", fontWeight: "800" },
  emptyText: { ...typography.body, color: colors.textSecondary },
  errorText: { ...typography.body, color: colors.critical },
});
