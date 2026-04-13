"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

export function useLogin() {
  const setSession = useAuthStore((state) => state.setSession);
  return useMutation({
    mutationFn: apiClient.login,
    onSuccess: setSession,
  });
}

export function useRegister() {
  const setSession = useAuthStore((state) => state.setSession);
  return useMutation({
    mutationFn: apiClient.register,
    onSuccess: setSession,
  });
}

export function useGoogleLogin() {
  const setSession = useAuthStore((state) => state.setSession);
  return useMutation({
    mutationFn: apiClient.googleLogin,
    onSuccess: setSession,
  });
}

export function useCurrentUser(enabled = true) {
  const token = useAuthStore((state) => state.accessToken);
  return useQuery({
    queryKey: ["current-user"],
    queryFn: apiClient.me,
    enabled: enabled && Boolean(token),
  });
}
