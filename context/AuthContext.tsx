"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { checkOnboardingStatus } from "@/lib/api";

interface AuthContextType {
  username: string | null;
  needsOnboarding: boolean;
  onboardingLoading: boolean;
  login: (username: string) => void;
  logout: () => void;
  completeOnboarding: () => void;
}

const AuthContext = createContext<AuthContextType>({
  username: null,
  needsOnboarding: false,
  onboardingLoading: false,
  login: () => {},
  logout: () => {},
  completeOnboarding: () => {},
});

const STORAGE_KEY = "veto_username";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [onboardingLoading, setOnboardingLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setUsername(stored);
      // Check onboarding status for returning users
      setOnboardingLoading(true);
      checkOnboardingStatus(stored)
        .then((res) => setNeedsOnboarding(res.needs_onboarding))
        .catch(() => setNeedsOnboarding(false))
        .finally(() => setOnboardingLoading(false));
    }
    setLoaded(true);
  }, []);

  const login = (name: string) => {
    localStorage.setItem(STORAGE_KEY, name);
    setUsername(name);
    // New login — check onboarding status
    setOnboardingLoading(true);
    checkOnboardingStatus(name)
      .then((res) => setNeedsOnboarding(res.needs_onboarding))
      .catch(() => setNeedsOnboarding(false))
      .finally(() => setOnboardingLoading(false));
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setUsername(null);
    setNeedsOnboarding(false);
  };

  const completeOnboarding = () => {
    setNeedsOnboarding(false);
  };

  if (!loaded) return null;

  return (
    <AuthContext.Provider
      value={{ username, needsOnboarding, onboardingLoading, login, logout, completeOnboarding }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
