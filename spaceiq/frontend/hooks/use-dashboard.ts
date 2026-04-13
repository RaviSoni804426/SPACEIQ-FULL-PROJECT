"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";

export function useRecentSearches(enabled = true) {
  return useQuery({
    queryKey: ["dashboard", "recent-searches"],
    queryFn: apiClient.recentSearches,
    enabled,
  });
}

export function useTrendingLocalities() {
  return useQuery({
    queryKey: ["dashboard", "trending-localities"],
    queryFn: apiClient.trendingLocalities,
  });
}
