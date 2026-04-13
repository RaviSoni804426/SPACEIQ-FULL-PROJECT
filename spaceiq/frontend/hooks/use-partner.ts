"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";

export function usePartnerSpaces(enabled = true) {
  return useQuery({
    queryKey: ["partner", "spaces"],
    queryFn: apiClient.partnerSpaces,
    enabled,
  });
}

export function usePartnerBookings(enabled = true) {
  return useQuery({
    queryKey: ["partner", "bookings"],
    queryFn: apiClient.partnerBookings,
    enabled,
  });
}

export function useCreateSpace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiClient.createSpace,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["partner", "spaces"] });
      void queryClient.invalidateQueries({ queryKey: ["spaces"] });
    },
  });
}
