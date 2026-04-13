"use client";

import Link from "next/link";
import { ArrowRight, Compass, Flame, MapPinned, Search, Ticket } from "lucide-react";
import { useMemo, useState } from "react";

import { useRecentSearches, useTrendingLocalities } from "@/hooks/use-dashboard";
import { SpaceGrid } from "@/components/spaces/space-grid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useMyBookings } from "@/hooks/use-bookings";
import { useSpaces } from "@/hooks/use-spaces";
import { currency } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { useUiStore } from "@/store/ui-store";

export default function DashboardPage() {
  const [search, setSearch] = useState("");
  const user = useAuthStore((state) => state.user);
  const recentlyViewedIds = useUiStore((state) => state.recentlyViewed);
  const bookings = useMyBookings(Boolean(user));
  const spaces = useSpaces();
  const recentSearches = useRecentSearches(Boolean(user));
  const trendingLocalities = useTrendingLocalities();

  const recommendedSpaces = useMemo(() => (spaces.data ?? []).slice(0, 4), [spaces.data]);
  const recentlyViewedSpaces = useMemo(() => {
    if (!spaces.data?.length || recentlyViewedIds.length === 0) {
      return [];
    }
    return recentlyViewedIds
      .map((id) => spaces.data.find((space) => space.id === id))
      .filter((space): space is NonNullable<typeof space> => Boolean(space));
  }, [recentlyViewedIds, spaces.data]);

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-[28px] bg-slate-950 text-white shadow-xl">
        <div className="grid gap-6 px-6 py-8 sm:px-8 sm:py-10 lg:grid-cols-[1.1fr_0.9fr] lg:px-10">
          <div className="space-y-6">
            <Badge className="border-orange-400/20 bg-orange-500/10 text-orange-200">Overview Dashboard</Badge>
            <div className="space-y-3">
              <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
                Find Your Perfect Space in Bangalore
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                Discover coworking spaces, sports venues, meeting rooms, and studios with live availability,
                payments, and an AI booking assistant.
              </p>
            </div>

            <form action="/explore" className="flex flex-col gap-3 rounded-3xl bg-white/10 p-3 backdrop-blur sm:flex-row">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  className="h-12 rounded-2xl border-white/10 bg-white pl-10"
                  name="search"
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="coworking in Indiranagar"
                  value={search}
                />
              </div>
              <Button className="h-12 rounded-2xl px-6" type="submit">
                Search now
              </Button>
            </form>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {[
              {
                label: "Total Bookings",
                value: user ? String(bookings.data?.length ?? 0) : "0",
                description: user ? "Your confirmed and upcoming reservations" : "Log in to track bookings",
                icon: Ticket,
              },
              {
                label: "Spaces Available",
                value: String(spaces.data?.length ?? 0),
                description: "Synced and bookable across Bangalore",
                icon: Compass,
              },
              {
                label: "Trending Areas",
                value: String(trendingLocalities.data?.length ?? 0),
                description: "Live hotspots from active inventory",
                icon: Flame,
              },
              {
                label: "Recent Searches",
                value: user ? String(recentSearches.data?.length ?? 0) : "0",
                description: user ? "Your latest live intent signals" : "Log in to personalize discovery",
                icon: MapPinned,
              },
            ].map((item) => (
              <Card className="border-white/10 bg-white/8 text-white shadow-none" key={item.label}>
                <CardContent className="space-y-4 p-5">
                  <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10">
                    <item.icon className="h-5 w-5 text-orange-200" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-slate-300">{item.label}</p>
                    <p className="text-2xl font-semibold text-white">{item.value}</p>
                    <p className="text-sm text-slate-400">{item.description}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold text-slate-950">Recommended for you</h2>
            <p className="text-sm text-slate-500">Fresh spaces with strong ratings and easy access across the city.</p>
          </div>
          <Link href="/explore">
            <Button variant="secondary">
              View all
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
        <SpaceGrid loading={spaces.isLoading} spaces={recommendedSpaces} />
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Trending in Bangalore</h2>
                <p className="text-sm text-slate-500">High-supply localities users can jump into right now.</p>
              </div>
              <Flame className="h-5 w-5 text-primary" />
            </div>
            {trendingLocalities.data && trendingLocalities.data.length > 0 ? (
              <div className="space-y-3">
                {trendingLocalities.data.map((area) => (
                  <Link
                    className="flex items-center justify-between rounded-2xl border border-border bg-slate-50 px-4 py-4 transition hover:border-orange-200 hover:bg-orange-50"
                    href={`/explore?locality=${encodeURIComponent(area.locality)}`}
                    key={area.locality}
                  >
                    <div>
                      <p className="font-medium text-slate-900">{area.locality}</p>
                      <p className="text-sm text-slate-500">
                        {area.space_count} spaces · avg {currency(area.average_price)}/hr
                      </p>
                    </div>
                    <span className="text-sm font-medium text-primary">Explore</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-border bg-slate-50 px-4 py-6 text-sm leading-7 text-slate-500">
                Sync more Google Places inventory to populate dynamic hotspots here.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Recently viewed</h2>
                <p className="text-sm text-slate-500">Pick up where you left off.</p>
              </div>
              <MapPinned className="h-5 w-5 text-primary" />
            </div>

            {recentlyViewedSpaces.length > 0 ? (
              <div className="space-y-3">
                {recentlyViewedSpaces.map((space) => (
                  <Link
                    className="flex items-center justify-between rounded-2xl border border-border bg-slate-50 px-4 py-4 transition hover:border-orange-200 hover:bg-orange-50"
                    href={`/spaces/${space.id}`}
                    key={space.id}
                  >
                    <div>
                      <p className="font-medium text-slate-900">{space.name}</p>
                      <p className="text-sm text-slate-500">{space.locality ?? "Bangalore"}</p>
                    </div>
                    <span className="text-sm font-medium text-primary">Open</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-border bg-slate-50 px-4 py-6 text-sm leading-7 text-slate-500">
                Explore spaces to build a personalized history here.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Recent searches</h2>
                <p className="text-sm text-slate-500">The latest intent signals shaping your recommendations.</p>
              </div>
              <Search className="h-5 w-5 text-primary" />
            </div>

            {!user ? (
              <div className="rounded-2xl border border-dashed border-border bg-slate-50 px-4 py-6 text-sm leading-7 text-slate-500">
                Log in and search from Explore to build a live personalized search history.
              </div>
            ) : recentSearches.data && recentSearches.data.length > 0 ? (
              <div className="space-y-3">
                {recentSearches.data.map((item) => (
                  <Link
                    className="block rounded-2xl border border-border bg-slate-50 px-4 py-4 transition hover:border-orange-200 hover:bg-orange-50"
                    href={`/explore?search=${encodeURIComponent(item.query)}${item.locality ? `&locality=${encodeURIComponent(item.locality)}` : ""}`}
                    key={`${item.query}-${item.created_at}`}
                  >
                    <p className="font-medium text-slate-900">{item.query}</p>
                    <p className="text-sm text-slate-500">{item.locality ?? "Bangalore"} search</p>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-border bg-slate-50 px-4 py-6 text-sm leading-7 text-slate-500">
                Search from Explore to see recent intent trails here.
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
