"use client";

import { useEffect, useMemo, useState } from "react";
import { X, Clock3, CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { RazorpayButton } from "@/components/payment/razorpay-button";
import { useSpace } from "@/hooks/use-spaces";
import { useHoldBooking } from "@/hooks/use-bookings";
import { useAuthStore } from "@/store/auth-store";
import { currency, formatTime } from "@/lib/utils";
import type { AIChatSpaceCard } from "@/types";

interface AiBookingModalProps {
  space: AIChatSpaceCard;
  onClose: () => void;
  onBooked: (bookingId: string, spaceName: string) => void;
}

export function AiBookingModal({ space, onClose, onBooked }: AiBookingModalProps) {
  const user = useAuthStore((s) => s.user);
  const today = new Date().toISOString().split("T")[0];
  const [selectedDate, setSelectedDate] = useState(today);
  const [selectedSlotIds, setSelectedSlotIds] = useState<string[]>([]);
  const [hold, setHold] = useState<{ holdId: string; expiresAt: string; totalAmount: number } | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [bookingId, setBookingId] = useState<string | null>(null);

  const spaceQuery = useSpace(space.id, selectedDate);
  const holdBooking = useHoldBooking();
  const spaceDetail = spaceQuery.data;

  // Reset slots when date changes
  useEffect(() => {
    setSelectedSlotIds([]);
    setHold(null);
  }, [selectedDate]);

  // Hold countdown
  useEffect(() => {
    if (!hold) { setRemainingSeconds(0); return; }
    const tick = () => {
      const diff = Math.max(0, Math.floor((new Date(hold.expiresAt).getTime() - Date.now()) / 1000));
      setRemainingSeconds(diff);
      if (diff === 0) setHold(null);
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [hold]);

  const availableSlots = spaceDetail?.available_slots ?? [];

  const selectedSlots = useMemo(
    () => availableSlots.filter((s) => selectedSlotIds.includes(s.id)),
    [availableSlots, selectedSlotIds],
  );

  const totalAmount = hold?.totalAmount ?? selectedSlots.length * Number(spaceDetail?.price_per_hour ?? space.price_per_hour);

  function toggleSlot(slotId: string) {
    const slotOrder = new Map(availableSlots.map((s, i) => [s.id, i]));
    setSelectedSlotIds((current) => {
      if (current.includes(slotId)) return current.filter((id) => id !== slotId);
      const next = [...current, slotId].sort((a, b) => (slotOrder.get(a) ?? 0) - (slotOrder.get(b) ?? 0));
      const indexes = next.map((id) => slotOrder.get(id) ?? 0);
      const consecutive = indexes.every((v, i) => i === 0 || v - indexes[i - 1] === 1);
      if (!consecutive) { toast.error("Select consecutive slots only."); return current; }
      return next;
    });
  }

  async function handleHold() {
    if (!user) { toast.error("Please log in to book."); return; }
    if (!selectedSlotIds.length) { toast.error("Select at least one slot."); return; }
    try {
      const res = await holdBooking.mutateAsync({
        space_id: space.id,
        date: selectedDate,
        slot_ids: selectedSlotIds,
      });
      setHold({ holdId: res.hold_id, expiresAt: res.expires_at, totalAmount: res.total_amount });
      toast.success("Slots held for 5 minutes.");
    } catch (err: any) {
      toast.error(err?.detail ?? "Could not hold slots.");
    }
  }

  function handleBookingSuccess(id: string) {
    setBookingId(id);
    onBooked(id, space.name);
  }

  const timeRange =
    selectedSlots.length > 0
      ? `${formatTime(selectedSlots[0].start_time)} – ${formatTime(selectedSlots[selectedSlots.length - 1].end_time)}`
      : null;

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/60 backdrop-blur-sm sm:items-center"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-t-[28px] bg-white shadow-2xl sm:rounded-[28px]">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-400">AI Booking</p>
            <h2 className="text-lg font-semibold text-slate-900 line-clamp-1">{space.name}</h2>
          </div>
          <button
            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 text-slate-500 hover:bg-slate-50"
            onClick={onClose}
            type="button"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {bookingId ? (
            /* Success state */
            <div className="flex flex-col items-center gap-4 py-8 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
                <CheckCircle2 className="h-8 w-8 text-emerald-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900">Booking Confirmed!</h3>
                <p className="mt-1 text-sm text-slate-500">Your slot at {space.name} is locked in.</p>
              </div>
              <div className="w-full rounded-2xl bg-slate-50 p-4 text-left text-sm">
                <div className="flex justify-between text-slate-600">
                  <span>Booking ID</span>
                  <span className="font-mono text-xs text-slate-900 max-w-[180px] truncate">{bookingId}</span>
                </div>
                {timeRange && (
                  <div className="mt-2 flex justify-between text-slate-600">
                    <span>Time</span>
                    <span className="font-medium text-slate-900">{timeRange}</span>
                  </div>
                )}
                <div className="mt-2 flex justify-between text-slate-600">
                  <span>Date</span>
                  <span className="font-medium text-slate-900">{selectedDate}</span>
                </div>
              </div>
              <Button className="w-full" onClick={onClose}>Done</Button>
            </div>
          ) : (
            <>
              {/* Date picker */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Select date</label>
                <input
                  type="date"
                  min={today}
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="flex h-10 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
              </div>

              {/* Slot picker */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  Available slots
                  {spaceQuery.isLoading && (
                    <Loader2 className="ml-2 inline h-3.5 w-3.5 animate-spin text-slate-400" />
                  )}
                </label>

                {!spaceQuery.isLoading && availableSlots.length === 0 && (
                  <p className="text-sm text-slate-500">No slots available for this date.</p>
                )}

                <div className="grid grid-cols-3 gap-2">
                  {availableSlots.map((slot) => {
                    const isSelected = selectedSlotIds.includes(slot.id);
                    const isBooked = slot.status === "booked";
                    const isHeld = slot.status === "held";
                    return (
                      <button
                        key={slot.id}
                        disabled={isBooked || isHeld}
                        onClick={() => toggleSlot(slot.id)}
                        type="button"
                        className={[
                          "rounded-xl border px-2 py-2 text-xs font-medium transition",
                          isSelected
                            ? "border-orange-400 bg-orange-50 text-orange-700"
                            : isBooked
                              ? "border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed line-through"
                              : isHeld
                                ? "border-amber-200 bg-amber-50 text-amber-600 cursor-not-allowed"
                                : "border-slate-200 bg-white text-slate-700 hover:border-orange-300 hover:bg-orange-50",
                        ].join(" ")}
                      >
                        {formatTime(slot.start_time)}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Summary */}
              {selectedSlots.length > 0 && (
                <div className="rounded-2xl bg-slate-50 p-4 text-sm space-y-2">
                  <div className="flex justify-between text-slate-600">
                    <span>Time</span>
                    <span className="font-medium text-slate-900">{timeRange}</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Slots</span>
                    <span className="font-medium text-slate-900">{selectedSlots.length}</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Total</span>
                    <span className="text-base font-semibold text-slate-900">{currency(totalAmount)}</span>
                  </div>
                </div>
              )}

              {/* Hold countdown */}
              {hold && (
                <div className="flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  <Clock3 className="h-4 w-4 flex-shrink-0" />
                  <span>
                    Hold expires in{" "}
                    <span className="font-semibold tabular-nums">
                      {String(Math.floor(remainingSeconds / 60)).padStart(2, "0")}:
                      {String(remainingSeconds % 60).padStart(2, "0")}
                    </span>
                  </span>
                </div>
              )}

              {/* Actions */}
              <div className="space-y-3">
                {!hold ? (
                  <Button
                    className="w-full"
                    size="lg"
                    disabled={holdBooking.isPending || selectedSlotIds.length === 0}
                    onClick={handleHold}
                  >
                    {holdBooking.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Hold Slots
                  </Button>
                ) : (
                  <RazorpayButton
                    holdId={hold.holdId}
                    label="Pay & Confirm Booking"
                    onSuccess={handleBookingSuccess}
                    redirectOnSuccess={false}
                  />
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
