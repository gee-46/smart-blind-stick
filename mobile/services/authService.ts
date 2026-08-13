import { api } from "./api";
import { clearTokens, saveTokens } from "../utils/tokenStorage";
import { Guardian, TokenPair } from "../types/api";

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

async function persistSession(tokens: TokenPair): Promise<Guardian> {
  await saveTokens(tokens.access_token, tokens.refresh_token);
  return tokens.guardian;
}

export async function register(input: RegisterInput): Promise<Guardian> {
  const response = await api.post<TokenPair>("/api/auth/register", input);
  return persistSession(response.data);
}

export async function login(input: LoginInput): Promise<Guardian> {
  const response = await api.post<TokenPair>("/api/auth/login", input);
  return persistSession(response.data);
}

export async function fetchCurrentGuardian(): Promise<Guardian> {
  const response = await api.get<Guardian>("/api/auth/me");
  return response.data;
}

export async function logout(): Promise<void> {
  try {
    await api.post("/api/auth/logout");
  } finally {
    // Always clear local tokens even if the network call fails --
    // the person expects "logout" to work offline too.
    await clearTokens();
  }
}
