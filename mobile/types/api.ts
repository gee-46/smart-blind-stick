/**
 * TypeScript types mirroring the real FastAPI backend Pydantic schemas.
 * Kept in lockstep with:
 *   app/schemas/auth.py
 *   app/schemas/guardian.py
 *   app/schemas/device.py
 *   app/schemas/location.py
 *   app/schemas/event.py
 *
 * If the backend contract changes, update this file to match -- these
 * types are not guessed, they were copied field-for-field from the
 * actual Pydantic models in the repository.
 */

// ---- Auth -------------------------------------------------------------

export interface Guardian {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  guardian: Guardian;
}

export interface AccessToken {
  access_token: string;
  token_type: string;
}

// ---- Device pairing -----------------------------------------------------

export interface PairedDevice {
  device_id: string;
  nickname: string | null;
  is_primary_guardian: boolean;
  paired_at: string;
  online: boolean;
  battery: number | null;
  gps_available: boolean;
  last_seen: string | null;
}

// ---- Device status (raw device endpoint) --------------------------------

export interface DeviceStatus {
  device_id: string;
  online: boolean;
  battery: number | null;
  gps_available: boolean;
  last_seen: string | null;
  last_fix_quality: number | null;
  last_satellites: number | null;
}

// ---- Location -------------------------------------------------------------

export interface LocationPoint {
  device_id: string;
  latitude: number;
  longitude: number;
  altitude: number | null;
  speed_kmh: number | null;
  satellites: number | null;
  fix_quality: number | null;
  timestamp: string;
}

export interface LocationHistoryItem {
  latitude: number;
  longitude: number;
  altitude: number | null;
  speed_kmh: number | null;
  satellites: number | null;
  fix_quality: number | null;
  timestamp: string;
}

// ---- Events / Safety / AI Vision / Sensors -------------------------------

export type RiskLevel = "safe" | "low" | "medium" | "high" | "critical";
export type EventSource = "ai_vision" | "sensor_fusion" | "safety_engine" | "manual" | string;

export interface EventOut {
  id: number;
  device_id: string;
  source: EventSource;
  event_type: string;
  risk_level: RiskLevel | null;
  message: string | null;
  extra: Record<string, unknown> | null;
  timestamp: string;
}

// ---- SOS ------------------------------------------------------------------

export interface SOSOut {
  success: boolean;
  message: string;
  event_id: number;
}

// ---- Emergency contacts -----------------------------------------------------

export interface Contact {
  id: number;
  name: string;
  phone: string;
  relationship_label: string | null;
  is_primary: boolean;
  created_at: string;
}

export interface ContactInput {
  name: string;
  phone: string;
  relationship_label?: string | null;
  is_primary?: boolean;
}

// ---- Push tokens -----------------------------------------------------------

export interface PushTokenResponse {
  success: boolean;
  message: string;
}

// ---- WebSocket messages ------------------------------------------------

export type WSMessageType =
  | "connected"
  | "device_online"
  | "device_offline"
  | "location_update"
  | "battery_update"
  | "object_detected"
  | "obstacle"
  | "danger"
  | "fall_detected"
  | "sos"
  | "safety_update"
  | string;

export interface WSMessage {
  type: WSMessageType;
  device_id?: string;
  [key: string]: unknown;
}

// ---- API error shape (FastAPI's default) -----------------------------------

export interface ApiErrorBody {
  detail?: string | { msg: string; loc: (string | number)[] }[];
}
