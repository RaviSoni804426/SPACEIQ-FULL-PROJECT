"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";

export function useMyBookings(enabled = true) {
  return useQuery({
    queryKey: ["bookings", "my"],
    queryFn: apiClient.myBookings,
    enabled,
  });
}

export function useBooking(bookingId: string, enabled = true) {
  return useQuery({
    queryKey: ["booking", bookingId],
    queryFn: () => apiClient.booking(bookingId),
    enabled: enabled && Boolean(bookingId),
  });
}

export function useHoldBooking() {
  return useMutation({
    mutationFn: apiClient.holdBooking,
  });
}

export function useInitPayment() {
  return useMutation({
    mutationFn: apiClient.initPayment,
  });
}

export function useVerifyPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiClient.verifyPayment,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["bookings", "my"] });
    },
  });
}

export function useCancelBooking() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bookingId, reason }: { bookingId: string; reason: string }) =>
      apiClient.cancelBooking(bookingId, reason),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["bookings", "my"] });
    },
  });
}

export function useCreateReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiClient.createReview,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["bookings", "my"] });
      void queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}
