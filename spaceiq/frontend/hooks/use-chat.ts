"use client";

import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/lib/api";

export function useChat() {
  return useMutation({
    mutationFn: apiClient.chat,
  });
}
