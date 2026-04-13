"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

type UiState = {
  recentlyViewed: string[];
  wishlist: string[];
  addViewed: (spaceId: string) => void;
  toggleWishlist: (spaceId: string) => void;
};

export const useUiStore = create<UiState>()(
  persist(
    (set, get) => ({
      recentlyViewed: [],
      wishlist: [],
      addViewed: (spaceId) => {
        const current = get().recentlyViewed.filter((item) => item !== spaceId);
        set({ recentlyViewed: [spaceId, ...current].slice(0, 3) });
      },
      toggleWishlist: (spaceId) => {
        const current = get().wishlist;
        set({
          wishlist: current.includes(spaceId)
            ? current.filter((item) => item !== spaceId)
            : [...current, spaceId],
        });
      },
    }),
    { name: "spacebook-ui" },
  ),
);
