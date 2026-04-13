"use client";

import { useMemo } from "react";

import { cn, formatTime } from "@/lib/utils";
import type { TimeSlot } from "@/types";

export function SlotPicker({
  slots,
  selected,
  onToggle,
}: {
  slots: TimeSlot[];
  selected: string[];
  onToggle: (slotId: string) => void;
}) {
  const selectedSet = useMemo(() => new Set(selected), [selected]);

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
      {slots.map((slot) => {
        const slotState =
          slot.status === "booked"
            ? "bg-slate-200 text-slate-400"
            : slot.status === "held"
              ? "bg-amber-100 text-amber-800"
              : selectedSet.has(slot.id)
                ? "bg-primary text-white"
                : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100";

        return (
          <button
            className={cn(
              "rounded-xl border border-border px-4 py-3 text-left text-sm transition-colors",
              slotState,
            )}
            disabled={slot.status !== "available"}
            key={slot.id}
            onClick={() => onToggle(slot.id)}
            type="button"
          >
            <p className="font-medium">{formatTime(slot.start_time)}</p>
            <p className="text-xs opacity-80">{formatTime(slot.end_time)}</p>
          </button>
        );
      })}
    </div>
  );
}
