"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Building2, DatabaseZap, Loader2, Store, Wallet } from "lucide-react";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { usePartnerBookings, usePartnerSpaces, useCreateSpace } from "@/hooks/use-partner";
import { useSyncGoogleSpaces } from "@/hooks/use-spaces";
import { currency, formatDate, formatTime } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

const AMENITIES = ["WiFi", "AC", "Parking", "Projector", "Cafeteria"];

const createSpaceSchema = z.object({
  name: z.string().min(3, "Enter a valid space name"),
  type: z.enum(["coworking", "sports", "meeting_room", "studio"]),
  address: z.string().min(8, "Enter a complete address"),
  locality: z.string().min(2, "Enter the locality"),
  description: z.string().min(24, "Add a clearer description"),
  price_per_hour: z.coerce.number().positive("Price per hour must be greater than zero"),
  image_urls: z.string().optional(),
  open_time: z.string().min(1, "Open time is required"),
  close_time: z.string().min(1, "Close time is required"),
});

type CreateSpaceValues = z.infer<typeof createSpaceSchema>;

export default function PartnerPage() {
  const user = useAuthStore((state) => state.user);
  const isPartnerView = user?.role === "partner" || user?.role === "admin";
  const partnerSpaces = usePartnerSpaces(isPartnerView);
  const partnerBookings = usePartnerBookings(isPartnerView);
  const createSpace = useCreateSpace();
  const syncGoogle = useSyncGoogleSpaces();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateSpaceValues>({
    resolver: zodResolver(createSpaceSchema),
    defaultValues: {
      name: "",
      type: "coworking",
      address: "",
      locality: "",
      description: "",
      price_per_hour: 500,
      image_urls: "",
      open_time: "06:00",
      close_time: "22:00",
    },
  });
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>(["WiFi", "AC"]);

  async function onSubmit(values: CreateSpaceValues) {
    try {
      await createSpace.mutateAsync({
        name: values.name,
        type: values.type,
        address: values.address,
        locality: values.locality,
        description: values.description,
        city: "Bangalore",
        price_per_hour: values.price_per_hour,
        amenities: selectedAmenities,
        images: values.image_urls
          ?.split("\n")
          .map((item) => item.trim())
          .filter(Boolean) ?? [],
        operating_hours: buildOperatingHours(values.open_time, values.close_time),
      });
      toast.success("Space created successfully.");
      reset();
      setSelectedAmenities(["WiFi", "AC"]);
    } catch (error) {
      const detail =
        error && typeof error === "object" && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : "Space could not be created.";
      toast.error(detail);
    }
  }

  async function handleSyncGoogle() {
    try {
      const response = await syncGoogle.mutateAsync();
      toast.success(
        response.detail ??
          `${response.synced} spaces synced ${response.source === "demo_seed" ? "from local demo inventory." : "from Google Places."}`,
      );
    } catch (error) {
      const detail =
        error && typeof error === "object" && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : "Google Places sync failed.";
      toast.error(detail);
    }
  }

  if (!user) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Log in to access Partner Hub</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          Partner workflows let you manage listings, watch bookings, and sync Google Places data into your catalog.
        </p>
        <Link href="/login">
          <Button>Go to login</Button>
        </Link>
      </div>
    );
  }

  if (!isPartnerView) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Partner access required</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          This page is ready for partner and admin users. Promote your account role in the backend to start listing spaces.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <section className="rounded-[28px] bg-slate-950 px-6 py-8 text-white shadow-xl sm:px-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight">Partner Hub</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
              Create listings, manage incoming demand, and seed real Bangalore inventory from Google Places.
            </p>
          </div>
          <Button disabled={syncGoogle.isPending} onClick={handleSyncGoogle} type="button" variant="secondary">
            {syncGoogle.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <DatabaseZap className="mr-2 h-4 w-4" />}
            Sync Google Places
          </Button>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardContent className="space-y-6 p-6">
            <div>
              <h2 className="text-2xl font-semibold text-slate-950">Add New Space</h2>
              <p className="mt-2 text-sm leading-7 text-slate-500">
                Use hosted image URLs and publish a listing immediately. Operating hours are applied across all days for this MVP flow.
              </p>
            </div>

            <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="name">
                  Name
                </label>
                <Input id="name" placeholder="The Pavilion Coworks" {...register("name")} />
                {errors.name ? <p className="text-sm text-red-500">{errors.name.message}</p> : null}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="type">
                  Type
                </label>
                <select className="flex h-10 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm" id="type" {...register("type")}>
                  <option value="coworking">Coworking</option>
                  <option value="sports">Sports</option>
                  <option value="meeting_room">Meeting Room</option>
                  <option value="studio">Studio</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="price_per_hour">
                  Price per hour
                </label>
                <Input id="price_per_hour" min="1" step="1" type="number" {...register("price_per_hour")} />
                {errors.price_per_hour ? <p className="text-sm text-red-500">{errors.price_per_hour.message}</p> : null}
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="address">
                  Address
                </label>
                <Input id="address" placeholder="Indiranagar 100 Feet Road, Bengaluru" {...register("address")} />
                {errors.address ? <p className="text-sm text-red-500">{errors.address.message}</p> : null}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="locality">
                  Locality
                </label>
                <Input id="locality" placeholder="Indiranagar" {...register("locality")} />
                {errors.locality ? <p className="text-sm text-red-500">{errors.locality.message}</p> : null}
              </div>

              <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700" htmlFor="open_time">
                      Open
                    </label>
                    <Input id="open_time" type="time" {...register("open_time")} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700" htmlFor="close_time">
                      Close
                    </label>
                    <Input id="close_time" type="time" {...register("close_time")} />
                  </div>
                </div>
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="description">
                  Description
                </label>
                <Textarea id="description" placeholder="Tell users what makes this space worth booking." {...register("description")} />
                {errors.description ? <p className="text-sm text-red-500">{errors.description.message}</p> : null}
              </div>

              <div className="space-y-3 md:col-span-2">
                <p className="text-sm font-medium text-slate-700">Amenities</p>
                <div className="flex flex-wrap gap-2">
                  {AMENITIES.map((amenity) => (
                    <button
                      className={`rounded-full border px-3 py-2 text-sm transition ${
                        selectedAmenities.includes(amenity)
                          ? "border-orange-300 bg-orange-50 text-orange-700"
                          : "border-border bg-white text-slate-600 hover:border-orange-200 hover:bg-orange-50"
                      }`}
                      key={amenity}
                      onClick={(event) => {
                        event.preventDefault();
                        setSelectedAmenities((current) =>
                          current.includes(amenity) ? current.filter((item) => item !== amenity) : [...current, amenity],
                        );
                      }}
                      type="button"
                    >
                      {amenity}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="image_urls">
                  Image URLs
                </label>
                <Textarea
                  id="image_urls"
                  placeholder="One hosted image URL per line"
                  {...register("image_urls")}
                />
              </div>

              <div className="md:col-span-2">
                <Button disabled={createSpace.isPending} type="submit">
                  {createSpace.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Store className="mr-2 h-4 w-4" />}
                  Add space
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="grid gap-6">
          <Card>
            <CardContent className="space-y-5 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-950">My Listings</h2>
                  <p className="text-sm text-slate-500">Active spaces and their current positioning.</p>
                </div>
                <Building2 className="h-5 w-5 text-primary" />
              </div>

              <div className="grid gap-3">
                {(partnerSpaces.data ?? []).map((space) => (
                  <div className="rounded-2xl border border-border bg-slate-50 p-4" key={space.id}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">{space.name}</p>
                        <p className="text-sm text-slate-500">
                          {space.locality ?? "Bangalore"} · {space.type.replace("_", " ")}
                        </p>
                      </div>
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                        {space.is_active ? "Active" : "Paused"}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
                      <span>{currency(space.price_per_hour)}/hr</span>
                      <span>{space.rating?.toFixed(1) ?? "New"} rating</span>
                      <span>{space.source}</span>
                    </div>
                  </div>
                ))}
                {partnerSpaces.data?.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border bg-slate-50 p-5 text-sm leading-7 text-slate-500">
                    No partner-managed listings yet. Sync Google Places or add your own space above.
                  </div>
                ) : null}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-5 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-950">Latest Bookings</h2>
                  <p className="text-sm text-slate-500">Incoming reservations across your spaces.</p>
                </div>
                <Wallet className="h-5 w-5 text-primary" />
              </div>

              <div className="grid gap-3">
                {(partnerBookings.data ?? []).slice(0, 6).map((booking) => (
                  <div className="rounded-2xl border border-border bg-white p-4" key={booking.id}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">{booking.space_name}</p>
                        <p className="text-sm text-slate-500">
                          {formatDate(booking.booking_date)} · {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                        </p>
                      </div>
                      <span className="text-sm font-semibold text-slate-900">{currency(booking.total_amount)}</span>
                    </div>
                  </div>
                ))}
                {partnerBookings.data?.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border bg-slate-50 p-5 text-sm leading-7 text-slate-500">
                    Bookings for your spaces will appear here once users complete payment.
                  </div>
                ) : null}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function buildOperatingHours(openTime: string, closeTime: string) {
  return {
    mon: [openTime, closeTime],
    tue: [openTime, closeTime],
    wed: [openTime, closeTime],
    thu: [openTime, closeTime],
    fri: [openTime, closeTime],
    sat: [openTime, closeTime],
    sun: [openTime, closeTime],
  };
}
