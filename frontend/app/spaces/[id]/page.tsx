"use client";

import Link from "next/link";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { Clock3, MapPin, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { SlotPicker } from "@/components/booking/slot-picker";
import { SpaceMap } from "@/components/spaces/space-map";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useHoldBooking } from "@/hooks/use-bookings";
import { useSpace } from "@/hooks/use-spaces";
import { cn, currency, formatTime } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

export default function SpaceDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
  const [selectedSlotIds, setSelectedSlotIds] = useState<string[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [expandedDescription, setExpandedDescription] = useState(false);
  const [hold, setHold] = useState<{ holdId: string; expiresAt: string; totalAmount: number } | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const holdBooking = useHoldBooking();
  const spaceQuery = useSpace(params.id, selectedDate);

  useEffect(() => {
    setSelectedSlotIds([]);
    setHold(null);
  }, [selectedDate, params.id]);

  useEffect(() => {
    if (!hold) {
      setRemainingSeconds(0);
      return;
    }

    const tick = () => {
      const diff = Math.max(0, Math.floor((new Date(hold.expiresAt).getTime() - Date.now()) / 1000));
      setRemainingSeconds(diff);
      if (diff === 0) {
        setHold(null);
      }
    };

    tick();
    const interval = window.setInterval(tick, 1000);
    return () => window.clearInterval(interval);
  }, [hold]);

  const space = spaceQuery.data;
  const selectedSlots = useMemo(() => {
    if (!space?.available_slots) {
      return [];
    }
    return space.available_slots.filter((slot) => selectedSlotIds.includes(slot.id));
  }, [selectedSlotIds, space?.available_slots]);

  function toggleSlot(slotId: string) {
    if (!space?.available_slots) {
      return;
    }

    const slotOrder = new Map(space.available_slots.map((slot, index) => [slot.id, index]));
    setSelectedSlotIds((current) => {
      const exists = current.includes(slotId);
      if (exists) {
        return current.filter((value) => value !== slotId);
      }

      const next = [...current, slotId].sort((left, right) => (slotOrder.get(left) ?? 0) - (slotOrder.get(right) ?? 0));
      const indexes = next.map((id) => slotOrder.get(id) ?? 0);
      const consecutive = indexes.every((value, index) => index === 0 || value - indexes[index - 1] === 1);
      if (!consecutive) {
        toast.error("Select consecutive hourly slots only.");
        return current;
      }
      return next;
    });
  }

  async function handleHold() {
    if (!user) {
      toast.error("Please log in to hold a slot.");
      router.push("/login");
      return;
    }
    if (!selectedSlotIds.length || !space) {
      toast.error("Choose at least one slot.");
      return;
    }

    try {
      const response = await holdBooking.mutateAsync({
        space_id: space.id,
        date: selectedDate,
        slot_ids: selectedSlotIds,
      });
      setHold({
        holdId: response.hold_id,
        expiresAt: response.expires_at,
        totalAmount: response.total_amount,
      });
      toast.success("Slots held for 5 minutes.");
    } catch (error) {
      const detail =
        error && typeof error === "object" && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : "The selected slots could not be held.";
      toast.error(detail);
    }
  }

  function proceedToPayment() {
    if (!hold) {
      toast.error("Hold the slots first to continue.");
      return;
    }
    router.push(
      `/booking/${params.id}?holdId=${encodeURIComponent(hold.holdId)}&date=${encodeURIComponent(selectedDate)}&slots=${encodeURIComponent(selectedSlotIds.join(","))}`,
    );
  }

  if (spaceQuery.isLoading) {
    return (
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
        <Skeleton className="h-[420px] w-full rounded-[28px]" />
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <Skeleton className="h-[640px] w-full rounded-[28px]" />
          <Skeleton className="h-[420px] w-full rounded-[28px]" />
        </div>
      </div>
    );
  }

  if (!space) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Space not found</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          This listing may have been removed, or the link may be incomplete.
        </p>
        <Link href="/explore">
          <Button>Back to explore</Button>
        </Link>
      </div>
    );
  }

  const description = space.description?.trim() || "This listing is synced from real space data for Bangalore and can be booked instantly when slots are available.";
  const descriptionPreview = expandedDescription ? description : `${description.slice(0, 220)}${description.length > 220 ? "..." : ""}`;
  const displayImages = space.images.length ? space.images : [];
  const timeRange =
    selectedSlots.length > 0
      ? `${formatTime(selectedSlots[0].start_time)} - ${formatTime(selectedSlots[selectedSlots.length - 1].end_time)}`
      : "Select slots";
  const totalPrice = hold?.totalAmount ?? selectedSlots.length * Number(space.price_per_hour);

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-[28px] border border-border bg-white shadow-sm">
        <div className="relative h-[360px] bg-gradient-to-br from-slate-100 via-slate-50 to-orange-100 sm:h-[440px]">
          {displayImages.length > 0 ? (
            <Image alt={space.name} className="h-full w-full object-cover" fill src={displayImages[currentImageIndex]} />
          ) : (
            <div className="flex h-full items-end bg-gradient-to-br from-slate-900/5 to-orange-400/20 p-8">
              <div className="space-y-2">
                <Badge>{space.type.replace("_", " ")}</Badge>
                <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-slate-950">{space.name}</h1>
              </div>
            </div>
          )}

          {displayImages.length > 1 ? (
            <div className="absolute bottom-6 left-6 flex gap-2">
              {displayImages.slice(0, 6).map((image, index) => (
                <button
                  className={cn(
                    "h-2.5 w-8 rounded-full transition",
                    currentImageIndex === index ? "bg-white" : "bg-white/40",
                  )}
                  key={image}
                  onClick={() => setCurrentImageIndex(index)}
                  type="button"
                />
              ))}
            </div>
          ) : null}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <section className="space-y-6">
          <div className="rounded-[28px] border border-border bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <Badge>{space.type.replace("_", " ")}</Badge>
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1 text-sm font-medium text-amber-700">
                    <Star className="h-4 w-4 fill-current" />
                    {space.rating?.toFixed(1) ?? "New"} · {space.total_reviews} reviews
                  </span>
                </div>
                <div className="space-y-2">
                  <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{space.name}</h1>
                  <p className="flex items-center gap-2 text-sm text-slate-500">
                    <MapPin className="h-4 w-4" />
                    {space.address || `${space.locality ?? "Bangalore"}, Bangalore`}
                  </p>
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 px-4 py-3 text-right">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Starting from</p>
                <p className="text-2xl font-semibold text-slate-950">{currency(space.price_per_hour)}/hr</p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-2">
              {space.amenities.map((amenity) => (
                <span className="rounded-full border border-border bg-slate-50 px-3 py-2 text-sm text-slate-600" key={amenity}>
                  {amenity}
                </span>
              ))}
            </div>

            <div className="mt-6 space-y-3">
              <h2 className="text-lg font-semibold text-slate-900">About this space</h2>
              <p className="text-sm leading-7 text-slate-600">{descriptionPreview}</p>
              {description.length > 220 ? (
                <button
                  className="text-sm font-medium text-primary hover:text-orange-500"
                  onClick={() => setExpandedDescription((current) => !current)}
                  type="button"
                >
                  {expandedDescription ? "Show less" : "Show more"}
                </button>
              ) : null}
            </div>
          </div>

          <Card>
            <CardContent className="space-y-5 p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold text-slate-950">Available slots</h2>
                  <p className="text-sm text-slate-500">Green is available, yellow is held, grey is booked.</p>
                </div>
                <InputDate value={selectedDate} onChange={setSelectedDate} />
              </div>

              <SlotPicker onToggle={toggleSlot} selected={selectedSlotIds} slots={space.available_slots ?? []} />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-4 p-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Location</h2>
                <p className="text-sm text-slate-500">Google Maps view for arrival and commute planning.</p>
              </div>
              <SpaceMap latitude={space.latitude} longitude={space.longitude} />
            </CardContent>
          </Card>
        </section>

        <aside className="lg:sticky lg:top-24 lg:h-fit">
          <Card className="overflow-hidden">
            <CardContent className="space-y-5 p-6">
              <div>
                <p className="text-sm font-medium text-slate-500">Selected slots</p>
                <p className="mt-2 text-lg font-semibold text-slate-950">{timeRange}</p>
                <p className="mt-1 text-sm text-slate-500">{selectedSlotIds.length} slot(s) selected</p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <div className="flex items-center justify-between text-sm text-slate-500">
                  <span>Date</span>
                  <span>{selectedDate}</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
                  <span>Total</span>
                  <span className="text-lg font-semibold text-slate-950">{currency(totalPrice)}</span>
                </div>
              </div>

              {hold ? (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-amber-800">
                    <Clock3 className="h-4 w-4" />
                    Hold expires in {formatCountdown(remainingSeconds)}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-amber-700">
                    Finish payment before the timer hits zero to keep these slots locked.
                  </p>
                </div>
              ) : null}

              <div className="space-y-3">
                <Button className="w-full" disabled={holdBooking.isPending || selectedSlotIds.length === 0} onClick={handleHold} size="lg" type="button">
                  Hold &amp; Proceed to Payment
                </Button>
                <Button className="w-full" disabled={!hold} onClick={proceedToPayment} size="lg" type="button" variant="secondary">
                  Open payment page
                </Button>
              </div>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function InputDate({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <input
      className="flex h-10 rounded-md border border-border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm"
      min={new Date().toISOString().split("T")[0]}
      onChange={(event) => onChange(event.target.value)}
      type="date"
      value={value}
    />
  );
}

function formatCountdown(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(totalSeconds % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
}
