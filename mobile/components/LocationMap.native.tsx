/**
 * Native (Android/iOS) implementation — real react-native-maps MapView.
 *
 * This file is only ever bundled for Android/iOS: Metro's platform
 * extension resolution picks `LocationMap.native.tsx` over any
 * `LocationMap.web.tsx` when building for those platforms, and picks
 * `LocationMap.web.tsx` instead when building for web -- so
 * react-native-maps is never imported/evaluated in the web bundle.
 * See LocationMap.web.tsx for why that matters.
 */
import React, { useRef } from "react";
import { Platform, StyleSheet, Text, View } from "react-native";
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from "react-native-maps";

import { colors, spacing, typography } from "../utils/theme";
import { LocationHistoryItem, LocationPoint } from "../types/api";

interface LocationMapProps {
  current: LocationPoint | null;
  history: LocationHistoryItem[];
}

export function LocationMap({ current, history }: LocationMapProps) {
  const mapRef = useRef<MapView | null>(null);

  if (!current) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>No data available</Text>
      </View>
    );
  }

  const region = {
    latitude: current.latitude,
    longitude: current.longitude,
    latitudeDelta: 0.01,
    longitudeDelta: 0.01,
  };

  const trail = history.map((point) => ({ latitude: point.latitude, longitude: point.longitude }));

  return (
    <MapView
      ref={mapRef}
      style={styles.map}
      provider={Platform.OS === "android" ? PROVIDER_GOOGLE : undefined}
      initialRegion={region}
      showsUserLocation={false}
      accessibilityLabel="Map showing the smart stick's live location"
    >
      <Marker
        coordinate={{ latitude: current.latitude, longitude: current.longitude }}
        title="Smart Blind Stick"
        description={`Last update: ${new Date(current.timestamp).toLocaleTimeString()}`}
        pinColor={colors.accent}
      />
      {trail.length > 1 && <Polyline coordinates={trail} strokeColor={colors.accent} strokeWidth={3} />}
    </MapView>
  );
}

const styles = StyleSheet.create({
  map: { flex: 1, minHeight: 320, borderRadius: 14, overflow: "hidden" },
  empty: {
    minHeight: 200,
    borderRadius: 14,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  emptyText: { ...typography.body, color: colors.textSecondary },
});
