import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import * as authService from "../services/authService";
import { getAccessToken } from "../utils/tokenStorage";
import { Guardian } from "../types/api";

interface AuthContextValue {
  guardian: Guardian | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: authService.RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  refreshGuardian: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [guardian, setGuardian] = useState<Guardian | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const bootstrap = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = await getAccessToken();
      if (!token) {
        setGuardian(null);
        return;
      }
      const current = await authService.fetchCurrentGuardian();
      setGuardian(current);
    } catch {
      // Token missing/expired/invalid -- treat as logged out rather than crashing.
      setGuardian(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const login = useCallback(async (email: string, password: string) => {
    const current = await authService.login({ email, password });
    setGuardian(current);
  }, []);

  const register = useCallback(async (input: authService.RegisterInput) => {
    const current = await authService.register(input);
    setGuardian(current);
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setGuardian(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      guardian,
      isLoading,
      isAuthenticated: guardian !== null,
      login,
      register,
      logout,
      refreshGuardian: bootstrap,
    }),
    [guardian, isLoading, login, register, logout, bootstrap]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
