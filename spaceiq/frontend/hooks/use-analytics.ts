"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";

export function useAnalyticsOverview(enabled = true) {
  return useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: apiClient.analyticsOverview,
    enabled,
  });
}

export function useBookingsByDay(enabled = true) {
  return useQuery({
    queryKey: ["analytics", "bookings-by-day"],
    queryFn: apiClient.bookingsByDay,
    enabled,
  });
}

export function useRevenueBySpace(enabled = true) {
  return useQuery({
    queryKey: ["analytics", "revenue-by-space"],
    queryFn: apiClient.revenueBySpace,
    enabled,
  });
}
