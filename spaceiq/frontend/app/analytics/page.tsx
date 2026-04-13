"use client";

import Link from "next/link";
import { BarChart3, Building2, IndianRupee, LineChart, Star } from "lucide-react";

import { BookingChart } from "@/components/analytics/booking-chart";
import { BookingTypeDonut, RevenueBarChart } from "@/components/analytics/revenue-chart";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAnalyticsOverview, useBookingsByDay, useRevenueBySpace } from "@/hooks/use-analytics";
import { currency } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

export default function AnalyticsPage() {
  const user = useAuthStore((state) => state.user);
  const allowed = user?.role === "partner" || user?.role === "admin";
  const overview = useAnalyticsOverview(Boolean(allowed));
  const bookingsByDay = useBookingsByDay(Boolean(allowed));
  const revenueBySpace = useRevenueBySpace(Boolean(allowed));

  if (!user) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Log in to view analytics</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          Analytics are available for partner and admin accounts once spaces and bookings are live.
        </p>
        <Link href="/login">
          <Button>Go to login</Button>
        </Link>
      </div>
    );
  }

  if (!allowed) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Partner analytics only</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          Switch this user to a partner or admin role to unlock revenue, booking, and performance dashboards.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <section className="rounded-[28px] bg-slate-950 px-6 py-8 text-white shadow-xl sm:px-8">
        <h1 className="text-4xl font-semibold tracking-tight">Analytics</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
          Revenue, bookings, ratings, and top-performing spaces in one clean operational view.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Total Revenue", value: currency(overview.data?.total_revenue ?? 0), icon: IndianRupee },
          { label: "Total Bookings", value: String(overview.data?.total_bookings ?? 0), icon: LineChart },
          { label: "Avg. Rating", value: (overview.data?.average_rating ?? 0).toFixed(1), icon: Star },
          { label: "Active Spaces", value: String(overview.data?.active_spaces ?? 0), icon: Building2 },
        ].map((item) => (
          <Card key={item.label}>
            <CardContent className="space-y-4 p-5">
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-orange-50 text-primary">
                <item.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{item.label}</p>
                <p className="mt-1 text-2xl font-semibold text-slate-950">{item.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-semibold text-slate-950">Bookings per day</h2>
                <p className="text-sm text-slate-500">Last 30 days</p>
              </div>
              <BarChart3 className="h-5 w-5 text-primary" />
            </div>
            <BookingChart data={bookingsByDay.data ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4 p-6">
            <h2 className="text-2xl font-semibold text-slate-950">Revenue by space</h2>
            <p className="text-sm text-slate-500">Top earning listings</p>
            <RevenueBarChart data={revenueBySpace.data ?? []} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardContent className="space-y-4 p-6">
            <h2 className="text-2xl font-semibold text-slate-950">Bookings by type</h2>
            <p className="text-sm text-slate-500">Revenue-weighted type distribution</p>
            <BookingTypeDonut data={revenueBySpace.data ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4 p-6">
            <h2 className="text-2xl font-semibold text-slate-950">Top performing spaces</h2>
            <div className="grid gap-3">
              {(revenueBySpace.data ?? []).map((space) => (
                <div className="rounded-2xl border border-border bg-slate-50 p-4" key={space.space_name}>
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-900">{space.space_name}</p>
                      <p className="text-sm text-slate-500 capitalize">{space.space_type.replace("_", " ")}</p>
                    </div>
                    <span className="text-sm font-semibold text-slate-900">{currency(space.value)}</span>
                  </div>
                </div>
              ))}
              {revenueBySpace.data?.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border bg-slate-50 p-5 text-sm leading-7 text-slate-500">
                  Confirmed bookings will populate this table automatically.
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
