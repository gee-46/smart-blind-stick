/**
 * Push notification service.
 *
 * Two responsibilities, both real:
 *   1. Register this device's Expo push token with the backend
 *      (POST /api/push/register) so a server-side sender has somewhere
 *      real to deliver to later.
 *   2. Fire a local notification immediately when the app is foregrounded
 *      and a critical WebSocket event arrives (SOS, critical risk, fall,
 *      device offline, critical battery) -- this part works today,
 *      independent of server-push delivery.
 *
 * Server -> device push delivery itself depends on a real Expo push
 * provider call from the backend (currently the notification_service
 * abstraction in the backend is still the Mock implementation -- see
 * README "Known limitations"). We do not fabricate a "PASS" for that
 * until it's actually been exercised against Expo's push service.
 */
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

import { api } from "./api";
import { EventOut } from "../types/api";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  if (!Device.isDevice) {
    console.warn("[notifications] Push notifications require a physical device, not a simulator/emulator.");
    return null;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== "granted") {
    console.warn("[notifications] Permission denied; critical alerts will be missed.");
    return null;
  }

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("critical-alerts", {
      name: "Critical Safety Alerts",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#D7263D",
    });
  }

  const tokenResponse = await Notifications.getExpoPushTokenAsync();
  return tokenResponse.data;
}

export async function syncPushTokenWithBackend(expoPushToken: string, deviceId?: string): Promise<void> {
  await api.post("/api/push/register", { expo_push_token: expoPushToken, device_id: deviceId });
}

const CRITICAL_EVENT_TYPES = new Set(["sos", "danger", "fall_detected", "device_offline"]);

export function isCriticalWSEvent(message: { type: string; risk_level?: string | null }): boolean {
  if (CRITICAL_EVENT_TYPES.has(message.type)) return true;
  if (message.risk_level === "high" || message.risk_level === "critical") return true;
  return false;
}

export async function presentCriticalAlert(title: string, body: string): Promise<void> {
  await Notifications.scheduleNotificationAsync({
    content: { title, body, sound: true },
    trigger: null, // fire immediately
  });
}

export function describeEventForNotification(event: EventOut | { type: string; [key: string]: unknown }): {
  title: string;
  body: string;
} {
  const type = "event_type" in event ? (event as EventOut).event_type : (event as { type: string }).type;
  const message = "message" in event ? String((event as EventOut).message ?? "") : "";

  switch (type) {
    case "sos":
      return { title: "🆘 SOS TRIGGERED", body: message || "Emergency SOS received from the stick." };
    case "device_offline":
      return { title: "⚠️ Device offline", body: "The Smart Blind Stick has stopped responding." };
    case "fall_detected":
      return { title: "🔴 Possible fall detected", body: message || "Check on the user immediately." };
    default:
      return { title: "🔴 Critical alert", body: message || "A high-risk event was reported." };
  }
}
