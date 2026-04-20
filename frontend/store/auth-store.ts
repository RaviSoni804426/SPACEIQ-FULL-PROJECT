"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { TokenPair, User } from "@/types";

const AUTH_STORAGE_KEY = "spaceiq-auth";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setSession: (payload: TokenPair) => void;
  setUser: (user: User) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: (payload) =>
        set({
          accessToken: payload.access_token,
          refreshToken: payload.refresh_token,
          user: payload.user,
        }),
      setUser: (user) => set((state) => ({ ...state, user })),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: AUTH_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

export function getAuthSnapshot() {
  return useAuthStore.getState();
}
