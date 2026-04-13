"use client";

import Link from "next/link";
import Image from "next/image";
import { CalendarDays, CircleSlash, History, Star, Ticket } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useCancelBooking, useCreateReview, useMyBookings } from "@/hooks/use-bookings";
import { currency, formatDate, formatTime } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import type { Booking } from "@/types";

type BookingTab = "upcoming" | "past" | "cancelled";

export default function MyBookingsPage() {
  const user = useAuthStore((state) => state.user);
  const bookingsQuery = useMyBookings(Boolean(user));
  const cancelBooking = useCancelBooking();
  const createReview = useCreateReview();
  const [activeTab, setActiveTab] = useState<BookingTab>("upcoming");
  const [bookingToCancel, setBookingToCancel] = useState<Booking | null>(null);
  const [bookingToReview, setBookingToReview] = useState<Booking | null>(null);
  const [reason, setReason] = useState("");
  const [reviewComment, setReviewComment] = useState("");
  const [reviewRating, setReviewRating] = useState(5);

  const bookings = useMemo(() => bookingsQuery.data ?? [], [bookingsQuery.data]);
  const filtered = useMemo(() => bookings.filter((booking) => getBookingTab(booking) === activeTab), [activeTab, bookings]);

  async function handleCancel() {
    if (!bookingToCancel || reason.trim().length < 3) {
      toast.error("Please add a short cancellation reason.");
      return;
    }

    try {
      await cancelBooking.mutateAsync({ bookingId: bookingToCancel.id, reason: reason.trim() });
      toast.success("Booking cancelled.");
      setBookingToCancel(null);
      setReason("");
    } catch (error) {
      const detail =
        error && typeof error === "object" && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : "Booking could not be cancelled.";
      toast.error(detail);
    }
  }

  async function handleReviewSubmit() {
    if (!bookingToReview) {
      return;
    }

    try {
      await createReview.mutateAsync({
        booking_id: bookingToReview.id,
        rating: reviewRating,
        comment: reviewComment.trim() || undefined,
      });
      toast.success("Thanks for sharing your review.");
      setBookingToReview(null);
      setReviewComment("");
      setReviewRating(5);
    } catch (error) {
      const detail =
        error && typeof error === "object" && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : "Review could not be submitted.";
      toast.error(detail);
    }
  }

  if (!user) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Log in to view your bookings</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          Upcoming reservations, past visits, and cancellations all appear here once you sign in.
        </p>
        <Link href="/login">
          <Button>Go to login</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <section className="rounded-[28px] bg-slate-950 px-6 py-8 text-white shadow-xl sm:px-8">
        <h1 className="text-4xl font-semibold tracking-tight">My Bookings</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
          Track your upcoming plans, revisit past sessions, and manage cancellations from one place.
        </p>
      </section>

      <div className="flex flex-wrap gap-3">
        {[
          { key: "upcoming", label: "Upcoming", icon: CalendarDays },
          { key: "past", label: "Past", icon: History },
          { key: "cancelled", label: "Cancelled", icon: CircleSlash },
        ].map((tab) => (
          <button
            className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition ${
              activeTab === tab.key
                ? "border-orange-300 bg-orange-50 text-orange-700"
                : "border-border bg-white text-slate-600 hover:border-orange-200 hover:bg-orange-50"
            }`}
            key={tab.key}
            onClick={() => setActiveTab(tab.key as BookingTab)}
            type="button"
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-primary">
              <Ticket className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">No bookings in this section yet</h2>
              <p className="mt-2 text-sm leading-7 text-slate-500">
                Explore Bangalore spaces and complete a payment to see bookings here.
              </p>
            </div>
            <Link href="/explore">
              <Button>Explore spaces</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filtered.map((booking) => (
            <Card key={booking.id}>
              <CardContent className="grid gap-4 p-5 md:grid-cols-[140px_minmax(0,1fr)_auto] md:items-center">
                <div className="relative overflow-hidden rounded-3xl bg-slate-100">
                  {booking.image_url ? (
                    <Image
                      alt={booking.space_name ?? "Booked space"}
                      className="h-full min-h-[120px] w-full object-cover"
                      fill
                      src={booking.image_url}
                    />
                  ) : (
                    <div className="flex min-h-[120px] items-end bg-gradient-to-br from-slate-900/5 to-orange-400/20 p-4">
                      <p className="text-lg font-semibold text-slate-900">{booking.space_name}</p>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-xl font-semibold text-slate-950">{booking.space_name}</h2>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(booking.status)}`}>
                      {booking.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500">{booking.locality ?? "Bangalore"}</p>
                  <p className="text-sm text-slate-600">
                    {formatDate(booking.booking_date)} · {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                  </p>
                  <p className="text-sm font-medium text-slate-900">{currency(booking.total_amount)}</p>
                </div>

                <div className="flex flex-wrap gap-3 md:justify-end">
                  {getBookingTab(booking) === "upcoming" && booking.status === "confirmed" ? (
                    <Button onClick={() => setBookingToCancel(booking)} type="button" variant="secondary">
                      Cancel Booking
                    </Button>
                  ) : null}
                  {getBookingTab(booking) === "past" ? (
                    booking.review_submitted ? (
                      <span className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700">
                        <Star className="h-4 w-4 fill-current" />
                        Reviewed {booking.review_rating ? `(${booking.review_rating}/5)` : ""}
                      </span>
                    ) : (
                      <Button onClick={() => setBookingToReview(booking)} type="button" variant="secondary">
                        Leave a Review
                      </Button>
                    )
                  ) : null}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {bookingToCancel ? (
        <div className="fixed inset-0 z-50 bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="mx-auto mt-12 w-full max-w-md rounded-[28px] bg-white p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-slate-950">Cancel booking</h2>
            <p className="mt-2 text-sm leading-7 text-slate-500">
              Share a quick reason so the cancellation is properly recorded.
            </p>
            <div className="mt-5">
              <Textarea onChange={(event) => setReason(event.target.value)} placeholder="Plans changed, timing issue, found another slot..." value={reason} />
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <Button onClick={() => setBookingToCancel(null)} type="button" variant="ghost">
                Close
              </Button>
              <Button disabled={cancelBooking.isPending} onClick={handleCancel} type="button">
                Confirm cancellation
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {bookingToReview ? (
        <div className="fixed inset-0 z-50 bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="mx-auto mt-12 w-full max-w-md rounded-[28px] bg-white p-6 shadow-xl">
            <h2 className="text-2xl font-semibold text-slate-950">Leave a review</h2>
            <p className="mt-2 text-sm leading-7 text-slate-500">
              Tell other Bangalore users what the experience was like at {bookingToReview.space_name}.
            </p>

            <div className="mt-5 flex gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  className={`inline-flex h-11 w-11 items-center justify-center rounded-2xl border transition ${
                    reviewRating >= value
                      ? "border-orange-300 bg-orange-50 text-orange-600"
                      : "border-border bg-white text-slate-400 hover:border-orange-200 hover:text-orange-500"
                  }`}
                  key={value}
                  onClick={() => setReviewRating(value)}
                  type="button"
                >
                  <Star className={`h-5 w-5 ${reviewRating >= value ? "fill-current" : ""}`} />
                </button>
              ))}
            </div>

            <div className="mt-5">
              <Textarea
                onChange={(event) => setReviewComment(event.target.value)}
                placeholder="Great WiFi, clean showers, easy parking, smooth check-in..."
                value={reviewComment}
              />
            </div>

            <div className="mt-5 flex justify-end gap-3">
              <Button onClick={() => setBookingToReview(null)} type="button" variant="ghost">
                Close
              </Button>
              <Button disabled={createReview.isPending} onClick={handleReviewSubmit} type="button">
                Submit review
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function getBookingTab(booking: Booking): BookingTab {
  if (booking.status === "cancelled") {
    return "cancelled";
  }

  const safeTime = booking.start_time.length === 5 ? `${booking.start_time}:00` : booking.start_time;
  const start = new Date(`${booking.booking_date}T${safeTime}`);
  return start.getTime() >= Date.now() ? "upcoming" : "past";
}

function statusClasses(status: Booking["status"]) {
  if (status === "confirmed") {
    return "bg-emerald-50 text-emerald-700";
  }
  if (status === "cancelled") {
    return "bg-red-50 text-red-600";
  }
  if (status === "completed") {
    return "bg-slate-100 text-slate-700";
  }
  return "bg-amber-50 text-amber-700";
}
