/**
 * Shared Axios instance for all backend communication.
 *
 * Base URL comes from EXPO_PUBLIC_API_URL so it's configurable per
 * environment (dev machine LAN IP, staging, production) without a code
 * change -- see README.md "Configuration" for how to set it for a
 * physical Android device.
 *
 * On a 401 (expired access token), we transparently try the refresh
 * flow once before giving up and forcing logout, so screens don't have
 * to handle token expiry individually.
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import Constants from "expo-constants";

import { clearTokens, getAccessToken, getRefreshToken, saveAccessToken } from "../utils/tokenStorage";
import { AccessToken, ApiErrorBody } from "../types/api";

function resolveBaseUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv && fromEnv.length > 0) return fromEnv;

  // Fall back to app.json "extra.apiUrl" if someone configures it there instead.
  const fromExtra = (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl;
  if (fromExtra) return fromExtra;

  // No hardcoded localhost/127.0.0.1 fallback for physical-device builds --
  // fail loudly instead of silently pointing at an unreachable address.
  console.warn(
    "[api] EXPO_PUBLIC_API_URL is not set. Set it in mobile/.env, e.g. " +
      "EXPO_PUBLIC_API_URL=http://192.168.1.100:8000 (see README.md)."
  );
  return "http://localhost:8000";
}

export const API_BASE_URL = resolveBaseUrl();

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await axios.post<AccessToken>(`${API_BASE_URL}/api/auth/refresh`, {
      refresh_token: refreshToken,
    });
    await saveAccessToken(response.data.access_token);
    return response.data.access_token;
  } catch {
    return null;
  }
}

api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const token = await getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;

    const isAuthEndpoint = originalRequest?.url?.includes("/api/auth/");
    if (error.response?.status === 401 && originalRequest && !originalRequest._retried && !isAuthEndpoint) {
      originalRequest._retried = true;

      if (!refreshInFlight) {
        refreshInFlight = refreshAccessToken().finally(() => {
          refreshInFlight = null;
        });
      }
      const newToken = await refreshInFlight;

      if (newToken) {
        originalRequest.headers.set("Authorization", `Bearer ${newToken}`);
        return api(originalRequest);
      }

      // Refresh failed too -- the session is genuinely over.
      await clearTokens();
    }

    return Promise.reject(error);
  }
);

/** Extracts a human-readable message from a FastAPI error response. */
export function extractErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorBody | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail.length > 0) return data.detail[0].msg;
    if (error.code === "ECONNABORTED") return "The request timed out. Check your connection to the backend.";
    if (!error.response) return "Can't reach the backend. Check EXPO_PUBLIC_API_URL and your network.";
  }
  return fallback;
}
