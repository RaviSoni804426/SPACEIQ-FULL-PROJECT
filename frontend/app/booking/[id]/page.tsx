"use client";

import Link from "next/link";
import Image from "next/image";
import { useParams, useSearchParams } from "next/navigation";
import { CalendarPlus, CheckCircle2, Clock3, Share2 } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { RazorpayButton } from "@/components/payment/razorpay-button";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBooking } from "@/hooks/use-bookings";
import { useSpace } from "@/hooks/use-spaces";
import { currency, formatDate, formatTime } from "@/lib/utils";

export default function BookingPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const holdId = searchParams.get("holdId") ?? "";
  const date = searchParams.get("date") ?? new Date().toISOString().split("T")[0];
  const selectedSlotIds = useMemo(
    () => searchParams.get("slots")?.split(",").filter(Boolean) ?? [],
    [searchParams],
  );
  const [bookingId, setBookingId] = useState<string | null>(null);
  const spaceQuery = useSpace(params.id, date);
  const bookingQuery = useBooking(bookingId ?? "", Boolean(bookingId));

  const space = spaceQuery.data;
  const selectedSlots = useMemo(() => {
    if (!space?.available_slots) {
      return [];
    }
    return selectedSlotIds
      .map((id) => space.available_slots?.find((slot) => slot.id === id))
      .filter((slot): slot is NonNullable<typeof slot> => Boolean(slot));
  }, [selectedSlotIds, space?.available_slots]);

  const totalAmount = selectedSlots.length * Number(space?.price_per_hour ?? 0);

  async function handleShare() {
    if (!bookingId) {
      return;
    }
    const shareText = `My SpaceIQ booking is confirmed. Booking ID: ${bookingId}`;
    if (navigator.share) {
      await navigator.share({
        title: "SpaceIQ Booking",
        text: shareText,
      });
      return;
    }
    await navigator.clipboard.writeText(shareText);
    toast.success("Booking details copied to clipboard.");
  }

  if (!holdId) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">A live slot hold is required</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          Start from a space detail page, hold the slot, and then continue to payment.
        </p>
        <Link href={`/spaces/${params.id}`}>
          <Button>Return to space</Button>
        </Link>
      </div>
    );
  }

  if (spaceQuery.isLoading) {
    return (
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
        <Skeleton className="h-28 w-full rounded-[28px]" />
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <Skeleton className="h-[420px] w-full rounded-[28px]" />
          <Skeleton className="h-[320px] w-full rounded-[28px]" />
        </div>
      </div>
    );
  }

  if (!space) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Booking details unavailable</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          We could not load the space tied to this hold. Please retry from the space detail page.
        </p>
      </div>
    );
  }

  const confirmedBooking = bookingQuery.data;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <section className="rounded-[28px] bg-slate-950 px-6 py-8 text-white shadow-xl sm:px-8">
        <Badge className="border-orange-400/20 bg-orange-500/10 text-orange-200">Booking &amp; Payment</Badge>
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-300">
          <span className="rounded-full bg-white/10 px-3 py-1.5">1. Confirm details</span>
          <span className="rounded-full bg-white/10 px-3 py-1.5">2. Razorpay checkout</span>
          <span className="rounded-full bg-white/10 px-3 py-1.5">3. Booking success</span>
        </div>
      </section>

      {bookingId && confirmedBooking ? (
        <section className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <Card className="overflow-hidden border-emerald-200 bg-emerald-50/60">
            <CardContent className="space-y-5 p-6">
              <div className="flex items-center gap-3">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500 text-white">
                  <CheckCircle2 className="h-6 w-6" />
                </div>
                <div>
                  <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Booking confirmed</h1>
                  <p className="text-sm text-slate-600">Your payment is verified and the slots are locked in.</p>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-white bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Booking ID</p>
                  <p className="mt-2 font-semibold text-slate-900">{confirmedBooking.id}</p>
                </div>
                <div className="rounded-2xl border border-white bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Payment ID</p>
                  <p className="mt-2 font-semibold text-slate-900">{confirmedBooking.razorpay_payment_id}</p>
                </div>
              </div>

              <div className="rounded-2xl border border-white bg-white p-4">
                <p className="font-semibold text-slate-900">{confirmedBooking.space_name}</p>
                <p className="mt-2 text-sm text-slate-500">
                  {formatDate(confirmedBooking.booking_date)} · {formatTime(confirmedBooking.start_time)} -{" "}
                  {formatTime(confirmedBooking.end_time)}
                </p>
                <p className="mt-1 text-sm text-slate-500">{confirmedBooking.locality ?? "Bangalore"}</p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button onClick={() => window.open(buildCalendarUrl(confirmedBooking.space_name ?? space.name, confirmedBooking.booking_date, confirmedBooking.start_time, confirmedBooking.end_time), "_blank", "noopener,noreferrer")} type="button" variant="secondary">
                  <CalendarPlus className="mr-2 h-4 w-4" />
                  Add to Calendar
                </Button>
                <Button onClick={handleShare} type="button" variant="secondary">
                  <Share2 className="mr-2 h-4 w-4" />
                  Share
                </Button>
                <Link href="/my-bookings">
                  <Button>View My Bookings</Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-4 p-6">
              <h2 className="text-xl font-semibold text-slate-950">What happens next</h2>
              <div className="space-y-3 text-sm leading-7 text-slate-600">
                <p>Your booking is stored with the verified Razorpay payment reference.</p>
                <p>You can manage cancellations and booking history from the My Bookings page.</p>
                <p>Need more time slots? Return to Explore and book another space.</p>
              </div>
            </CardContent>
          </Card>
        </section>
      ) : (
        <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <Card>
            <CardContent className="space-y-6 p-6">
              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Confirm your booking</h1>
                <p className="text-sm leading-7 text-slate-500">
                  Review the held slots below, then continue to Razorpay checkout.
                </p>
              </div>

              <div className="grid gap-4 rounded-[28px] bg-slate-50 p-4 sm:grid-cols-[160px_minmax(0,1fr)]">
                <div className="relative overflow-hidden rounded-3xl bg-slate-200">
                  {space.images[0] ? (
                    <Image alt={space.name} className="h-full w-full object-cover" fill src={space.images[0]} />
                  ) : (
                    <div className="flex h-full min-h-[160px] items-end bg-gradient-to-br from-slate-900/5 to-orange-400/20 p-4">
                      <p className="text-lg font-semibold text-slate-900">{space.name}</p>
                    </div>
                  )}
                </div>
                <div className="space-y-3 py-2">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{space.type.replace("_", " ")}</p>
                    <h2 className="mt-2 text-2xl font-semibold text-slate-950">{space.name}</h2>
                    <p className="mt-2 text-sm text-slate-500">{space.address || `${space.locality ?? "Bangalore"}, Bangalore`}</p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white bg-white p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Booking date</p>
                      <p className="mt-2 font-semibold text-slate-900">{formatDate(date)}</p>
                    </div>
                    <div className="rounded-2xl border border-white bg-white p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Slots</p>
                      <p className="mt-2 font-semibold text-slate-900">
                        {selectedSlots.length > 0
                          ? `${formatTime(selectedSlots[0].start_time)} - ${formatTime(selectedSlots[selectedSlots.length - 1].end_time)}`
                          : "No slots selected"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h2 className="text-lg font-semibold text-slate-900">Selected slots</h2>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {selectedSlots.map((slot) => (
                    <div className="rounded-2xl border border-border bg-white p-4" key={slot.id}>
                      <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
                        <Clock3 className="h-4 w-4 text-primary" />
                        {formatTime(slot.start_time)} - {formatTime(slot.end_time)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <aside className="lg:sticky lg:top-24 lg:h-fit">
            <Card>
              <CardContent className="space-y-5 p-6">
                <div>
                  <p className="text-sm font-medium text-slate-500">Amount payable</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-950">{currency(totalAmount)}</p>
                </div>

                <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
                  <div className="flex items-center justify-between">
                    <span>Rate</span>
                    <span>{currency(space.price_per_hour)}/hr</span>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <span>Slots</span>
                    <span>{selectedSlots.length}</span>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <span>Hold ID</span>
                    <span className="max-w-[160px] truncate">{holdId}</span>
                  </div>
                </div>

                <RazorpayButton holdId={holdId} label="Pay with Razorpay" onSuccess={setBookingId} redirectOnSuccess={false} />

                <p className="text-xs leading-6 text-slate-500">
                  Razorpay test and live mode both work through the same flow once environment keys are configured.
                </p>
              </CardContent>
            </Card>
          </aside>
        </section>
      )}
    </div>
  );
}

function buildCalendarUrl(title: string, bookingDate: string, startTime: string, endTime: string) {
  const start = buildCalendarDate(bookingDate, startTime);
  const end = buildCalendarDate(bookingDate, endTime);
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: title,
    dates: `${start}/${end}`,
    details: "Booked with SpaceIQ",
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

function buildCalendarDate(date: string, time: string) {
  const safeTime = time.length === 5 ? `${time}:00` : time;
  return new Date(`${date}T${safeTime}`)
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}Z$/, "Z");
}
