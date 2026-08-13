/**
 * Secure token storage. Access + refresh tokens are the only sensitive
 * secrets the app holds, so they go in SecureStore (Keychain/Keystore),
 * never AsyncStorage and never in plain JS memory-only state that could
 * be lost or logged accidentally.
 */
import * as SecureStore from "expo-secure-store";

const ACCESS_TOKEN_KEY = "drishtiguard_access_token";
const REFRESH_TOKEN_KEY = "drishtiguard_refresh_token";

export async function saveTokens(accessToken: string, refreshToken: string): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function saveAccessToken(accessToken: string): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken);
}

export async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}
