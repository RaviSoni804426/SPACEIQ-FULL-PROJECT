"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";

export function useSpaces(params?: Record<string, string | number | string[] | undefined | null>) {
  return useQuery({
    queryKey: ["spaces", params],
    queryFn: () => apiClient.spaces(params),
  });
}

export function useSpace(spaceId: string, date?: string) {
  return useQuery({
    queryKey: ["space", spaceId, date],
    queryFn: () => apiClient.space(spaceId, date),
    enabled: Boolean(spaceId),
  });
}
