import React from "react";
import { Stack } from "expo-router";

import { colors } from "../../utils/theme";

export default function AppLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.textPrimary,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="pairing" options={{ title: "Pair a Device" }} />
      <Stack.Screen name="dashboard" options={{ title: "Dashboard", headerShown: false }} />
      <Stack.Screen name="location" options={{ title: "Live Location", headerShown: false }} />
      <Stack.Screen name="safety" options={{ title: "Safety" }} />
      <Stack.Screen name="events" options={{ title: "Event History", headerShown: false }} />
      <Stack.Screen name="sos" options={{ title: "Emergency SOS", headerShown: false }} />
      <Stack.Screen name="contacts" options={{ title: "Emergency Contacts" }} />
      <Stack.Screen name="settings" options={{ title: "Settings", headerShown: false }} />
    </Stack>
  );
}
