"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { UserPublic } from "@/types/api";
import { authApi, getAccessToken } from "@/lib/api-client";

interface AuthContextType {
  user: UserPublic | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  sessionExpiryWarning: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, displayName: string) => Promise<void>;
  logout: () => Promise<void>;
  dismissWarning: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionExpiryWarning, setSessionExpiryWarning] = useState(false);
  const router = useRouter();

  // Initial silent auth check via refresh token cookie
  useEffect(() => {
    let isMounted = true;
    async function initAuth() {
      try {
        const tokenRes = await authApi.refresh();
        if (isMounted && tokenRes?.user) {
          setUser(tokenRes.user);
        }
      } catch {
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    initAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  // Monitor session lifetime (warn at 25 minutes of inactivity)
  useEffect(() => {
    if (!user) return;
    const warnTimer = setTimeout(() => {
      setSessionExpiryWarning(true);
    }, 25 * 60 * 1000); // 25 minutes

    const logoutTimer = setTimeout(() => {
      logout();
    }, 30 * 60 * 1000); // 30 minutes

    return () => {
      clearTimeout(warnTimer);
      clearTimeout(logoutTimer);
    };
  }, [user]);

  const login = async (username: string, password: string) => {
    const data = await authApi.login({ username, password });
    setUser(data.user);
    setSessionExpiryWarning(false);
    if (data.user.role === "doctor") {
      router.push("/queue");
    } else {
      router.push("/cases");
    }
  };

  const register = async (username: string, password: string, displayName: string) => {
    await authApi.register({
      username,
      password,
      display_name: displayName,
    });
    // Auto-login upon registration
    await login(username, password);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      setSessionExpiryWarning(false);
      router.push("/login");
    }
  };

  const dismissWarning = async () => {
    setSessionExpiryWarning(false);
    try {
      await authApi.refresh();
    } catch {
      logout();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        sessionExpiryWarning,
        login,
        register,
        logout,
        dismissWarning,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
