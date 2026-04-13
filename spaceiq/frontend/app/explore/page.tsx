"use client";

import Link from "next/link";
import { Filter, Search, SlidersHorizontal, X } from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { SpaceGrid } from "@/components/spaces/space-grid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useSpaces } from "@/hooks/use-spaces";
import { cn, currency } from "@/lib/utils";
import type { SpaceType } from "@/types";

const TYPE_OPTIONS: { label: string; value: "all" | SpaceType }[] = [
  { label: "All", value: "all" },
  { label: "Coworking", value: "coworking" },
  { label: "Sports", value: "sports" },
  { label: "Meeting Room", value: "meeting_room" },
  { label: "Studio", value: "studio" },
];

const LOCALITIES = ["HSR Layout", "Indiranagar", "Koramangala", "Whitefield", "Jayanagar", "BTM Layout"];
const AMENITIES = ["WiFi", "AC", "Parking", "Projector", "Cafeteria"];
const SEARCH_PLACEHOLDERS = ["coworking in Indiranagar...", "football turf near me...", "meeting room HSR..."];

export default function ExplorePage() {
  const searchParams = useSearchParams();
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || searchParams.get("search_query") || "");
  const [selectedType, setSelectedType] = useState<"all" | SpaceType>("all");
  const [selectedLocalities, setSelectedLocalities] = useState<string[]>(
    searchParams.get("locality") ? [searchParams.get("locality") as string] : [],
  );
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const [priceMin, setPriceMin] = useState(0);
  const [priceMax, setPriceMax] = useState(2000);
  const [rating, setRating] = useState<number | null>(null);
  const [date, setDate] = useState("");
  const [sort, setSort] = useState("relevance");
  const deferredSearch = useDeferredValue(searchInput);
  const debouncedSearch = useDebouncedValue(deferredSearch, 300);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setPlaceholderIndex((current) => (current + 1) % SEARCH_PLACEHOLDERS.length);
    }, 2500);
    return () => window.clearInterval(interval);
  }, []);

  const params = useMemo(
    () => ({
      search_query: debouncedSearch || undefined,
      type: selectedType === "all" ? undefined : selectedType,
      locality: selectedLocalities.length ? selectedLocalities : undefined,
      price_min: priceMin > 0 ? priceMin : undefined,
      price_max: priceMax < 2000 ? priceMax : undefined,
      rating: rating ?? undefined,
      amenities: selectedAmenities.length ? selectedAmenities : undefined,
      date: date || undefined,
      sort,
    }),
    [date, debouncedSearch, priceMax, priceMin, rating, selectedAmenities, selectedLocalities, selectedType, sort],
  );

  const spaces = useSpaces(params);
  const instantResults = useMemo(() => (spaces.data ?? []).slice(0, 5), [spaces.data]);

  function toggleLocality(locality: string) {
    setSelectedLocalities((current) =>
      current.includes(locality) ? current.filter((item) => item !== locality) : [...current, locality],
    );
  }

  function toggleAmenity(amenity: string) {
    setSelectedAmenities((current) =>
      current.includes(amenity) ? current.filter((item) => item !== amenity) : [...current, amenity],
    );
  }

  function clearFilters() {
    setSelectedType("all");
    setSelectedLocalities([]);
    setSelectedAmenities([]);
    setPriceMin(0);
    setPriceMax(2000);
    setRating(null);
    setDate("");
    setSort("relevance");
  }

  const filterSidebar = (
    <Card className="h-fit lg:sticky lg:top-24">
      <CardContent className="space-y-6 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-primary" />
            <h2 className="font-semibold text-slate-900">Filters</h2>
          </div>
          <button className="text-sm font-medium text-slate-500 hover:text-slate-900" onClick={clearFilters} type="button">
            Reset
          </button>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-900">Type</p>
          <div className="flex flex-wrap gap-2">
            {TYPE_OPTIONS.map((option) => (
              <button
                className={cn(
                  "rounded-full border px-3 py-2 text-sm transition",
                  selectedType === option.value
                    ? "border-orange-300 bg-orange-50 text-orange-700"
                    : "border-border bg-white text-slate-600 hover:border-orange-200 hover:bg-orange-50",
                )}
                key={option.value}
                onClick={() => setSelectedType(option.value)}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-900">Locality</p>
          <div className="flex flex-wrap gap-2">
            {LOCALITIES.map((locality) => (
              <button
                className={cn(
                  "rounded-full border px-3 py-2 text-sm transition",
                  selectedLocalities.includes(locality)
                    ? "border-orange-300 bg-orange-50 text-orange-700"
                    : "border-border bg-white text-slate-600 hover:border-orange-200 hover:bg-orange-50",
                )}
                key={locality}
                onClick={() => toggleLocality(locality)}
                type="button"
              >
                {locality}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-900">Price range</p>
            <span className="text-xs text-slate-500">
              {currency(priceMin)} - {currency(priceMax)}
            </span>
          </div>
          <div className="space-y-4">
            <input
              className="w-full accent-orange-500"
              max={2000}
              min={0}
              onChange={(event) => setPriceMin(Math.min(Number(event.target.value), priceMax))}
              type="range"
              value={priceMin}
            />
            <input
              className="w-full accent-orange-500"
              max={2000}
              min={0}
              onChange={(event) => setPriceMax(Math.max(Number(event.target.value), priceMin))}
              type="range"
              value={priceMax}
            />
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-900">Rating</p>
          <div className="flex flex-wrap gap-2">
            {[3, 4, 4.5].map((value) => (
              <button
                className={cn(
                  "rounded-full border px-3 py-2 text-sm transition",
                  rating === value
                    ? "border-orange-300 bg-orange-50 text-orange-700"
                    : "border-border bg-white text-slate-600 hover:border-orange-200 hover:bg-orange-50",
                )}
                key={value}
                onClick={() => setRating(rating === value ? null : value)}
                type="button"
              >
                {value}+ stars
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-900">Amenities</p>
          <div className="grid gap-2">
            {AMENITIES.map((amenity) => (
              <label className="flex items-center gap-3 text-sm text-slate-600" key={amenity}>
                <input
                  checked={selectedAmenities.includes(amenity)}
                  className="h-4 w-4 rounded border-border accent-orange-500"
                  onChange={() => toggleAmenity(amenity)}
                  type="checkbox"
                />
                {amenity}
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-900">Date</p>
          <Input min={new Date().toISOString().split("T")[0]} onChange={(event) => setDate(event.target.value)} type="date" value={date} />
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-slate-900">Sort</p>
          <select
            className="flex h-10 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm"
            onChange={(event) => setSort(event.target.value)}
            value={sort}
          >
            <option value="relevance">Relevance</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="rating">Rating</option>
            <option value="distance">Distance</option>
          </select>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 rounded-[28px] bg-slate-950 px-6 py-8 text-white shadow-xl sm:px-8">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <Badge className="border-orange-400/20 bg-orange-500/10 text-orange-200">Explore &amp; Book</Badge>
            <h1 className="text-4xl font-semibold tracking-tight">Search live spaces across Bangalore</h1>
            <p className="max-w-3xl text-sm leading-7 text-slate-300">
              Discover bookable coworking, sports venues, studios, and meeting rooms with price, rating, amenity,
              and date filters.
            </p>
          </div>
          <Button className="lg:hidden" onClick={() => setMobileFiltersOpen(true)} variant="secondary">
            <SlidersHorizontal className="mr-2 h-4 w-4" />
            Filters
          </Button>
        </div>

        <div className="relative">
          <div className="relative">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              className="h-14 rounded-2xl border-white/10 bg-white pl-10 text-slate-900"
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder={SEARCH_PLACEHOLDERS[placeholderIndex]}
              value={searchInput}
            />
          </div>

          {searchInput.trim() && instantResults.length > 0 ? (
            <div className="absolute z-20 mt-3 w-full rounded-3xl border border-border bg-white p-3 text-slate-900 shadow-xl">
              <p className="px-3 pb-2 text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Top matches</p>
              <div className="grid gap-1">
                {instantResults.map((space) => (
                  <Link
                    className="flex items-center justify-between rounded-2xl px-3 py-3 transition hover:bg-orange-50"
                    href={`/spaces/${space.id}`}
                    key={space.id}
                  >
                    <div>
                      <p className="font-medium text-slate-900">{space.name}</p>
                      <p className="text-sm text-slate-500">
                        {space.locality ?? "Bangalore"} · {currency(space.price_per_hour)}/hr
                      </p>
                    </div>
                    <span className="text-sm font-medium text-primary">Open</span>
                  </Link>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[290px_minmax(0,1fr)]">
        <aside className="hidden lg:block">{filterSidebar}</aside>

        <section className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm text-slate-500">
                {spaces.data?.length ?? 0} spaces found {debouncedSearch ? `for "${debouncedSearch}"` : "across Bangalore"}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedLocalities.map((locality) => (
                <button
                  className="inline-flex items-center gap-2 rounded-full border border-orange-200 bg-orange-50 px-3 py-1.5 text-sm text-orange-700"
                  key={locality}
                  onClick={() => toggleLocality(locality)}
                  type="button"
                >
                  {locality}
                  <X className="h-3.5 w-3.5" />
                </button>
              ))}
              {selectedAmenities.map((amenity) => (
                <button
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600"
                  key={amenity}
                  onClick={() => toggleAmenity(amenity)}
                  type="button"
                >
                  {amenity}
                  <X className="h-3.5 w-3.5" />
                </button>
              ))}
            </div>
          </div>

          <SpaceGrid loading={spaces.isLoading} spaces={spaces.data ?? []} />
        </section>
      </div>

      {mobileFiltersOpen ? (
        <div className="fixed inset-0 z-50 bg-slate-950/60 p-4 backdrop-blur-sm lg:hidden">
          <div className="mx-auto mt-8 max-h-[85vh] w-full max-w-md overflow-y-auto">
            <div className="mb-3 flex justify-end">
              <button
                className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-white text-slate-900"
                onClick={() => setMobileFiltersOpen(false)}
                type="button"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            {filterSidebar}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function useDebouncedValue<T>(value: T, delay: number) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [delay, value]);

  return debounced;
}
