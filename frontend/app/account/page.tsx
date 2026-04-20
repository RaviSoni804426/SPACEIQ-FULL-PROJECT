"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { BellRing, Heart, Loader2, UserCircle2 } from "lucide-react";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api";
import { currency } from "@/lib/utils";
import { useCurrentUser } from "@/hooks/use-auth";
import { useMyBookings } from "@/hooks/use-bookings";
import { useSpaces } from "@/hooks/use-spaces";
import { useAuthStore } from "@/store/auth-store";
import { useUiStore } from "@/store/ui-store";

const profileSchema = z.object({
  full_name: z.string().min(2, "Enter your full name"),
  phone: z.string().optional().or(z.literal("")),
  avatar_url: z.string().url("Enter a valid image URL").optional().or(z.literal("")),
});

type ProfileValues = z.infer<typeof profileSchema>;

export default function AccountPage() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const logout = useAuthStore((state) => state.logout);
  const wishlist = useUiStore((state) => state.wishlist);
  const currentUser = useCurrentUser(Boolean(user));
  const bookings = useMyBookings(Boolean(user));
  const spaces = useSpaces();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      phone: "",
      avatar_url: "",
    },
  });
  const updateProfile = useMutation({
    mutationFn: apiClient.updateProfile,
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
      void queryClient.invalidateQueries({ queryKey: ["current-user"] });
    },
  });

  useEffect(() => {
    const source = currentUser.data ?? user;
    if (!source) {
      return;
    }
    reset({
      full_name: source.full_name,
      phone: source.phone ?? "",
      avatar_url: source.avatar_url ?? "",
    });
  }, [currentUser.data, reset, user]);

  const wishlistSpaces = (spaces.data ?? []).filter((space) => wishlist.includes(space.id));
  const totalSpend = (bookings.data ?? []).reduce((sum, booking) => sum + Number(booking.total_amount), 0);

  async function onSubmit(values: ProfileValues) {
    try {
      await updateProfile.mutateAsync({
        full_name: values.full_name,
        phone: values.phone || null,
        avatar_url: values.avatar_url || null,
      });
      toast.success("Profile updated.");
    } catch (error) {
      const detail =
        error && typeof error === "object" && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : "Profile update failed.";
      toast.error(detail);
    }
  }

  if (!user) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Log in to manage your account</h1>
        <p className="max-w-xl text-sm leading-7 text-slate-500">
          Update your profile, review your booking history, and manage saved spaces after signing in.
        </p>
        <Link href="/login">
          <Button>Go to login</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <section className="rounded-[28px] bg-slate-950 px-6 py-8 text-white shadow-xl sm:px-8">
        <h1 className="text-4xl font-semibold tracking-tight">Account</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
          Manage your profile, preferences, saved spaces, and booking history in one place.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
        <Card>
          <CardContent className="space-y-6 p-6">
            <div className="flex items-center gap-4">
              <div className="inline-flex h-16 w-16 items-center justify-center overflow-hidden rounded-3xl bg-orange-50 text-primary">
                {user.avatar_url ? (
                  <Image alt={user.full_name} className="h-full w-full object-cover" height={64} src={user.avatar_url} width={64} />
                ) : (
                  <UserCircle2 className="h-8 w-8" />
                )}
              </div>
              <div>
                <h2 className="text-2xl font-semibold text-slate-950">{user.full_name}</h2>
                <p className="text-sm text-slate-500">{user.email}</p>
              </div>
            </div>

            <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="full_name">
                  Full name
                </label>
                <Input id="full_name" {...register("full_name")} />
                {errors.full_name ? <p className="text-sm text-red-500">{errors.full_name.message}</p> : null}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="phone">
                  Phone
                </label>
                <Input id="phone" {...register("phone")} />
                {errors.phone ? <p className="text-sm text-red-500">{errors.phone.message}</p> : null}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="avatar_url">
                  Avatar URL
                </label>
                <Input id="avatar_url" placeholder="https://..." {...register("avatar_url")} />
                {errors.avatar_url ? <p className="text-sm text-red-500">{errors.avatar_url.message}</p> : null}
              </div>

              <div className="md:col-span-2">
                <Button disabled={updateProfile.isPending} type="submit">
                  {updateProfile.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Save profile
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="grid gap-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardContent className="space-y-3 p-5">
                <Heart className="h-5 w-5 text-primary" />
                <p className="text-sm text-slate-500">Saved spaces</p>
                <p className="text-2xl font-semibold text-slate-950">{wishlist.length}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="space-y-3 p-5">
                <BellRing className="h-5 w-5 text-primary" />
                <p className="text-sm text-slate-500">Booking history value</p>
                <p className="text-2xl font-semibold text-slate-950">{currency(totalSpend)}</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardContent className="space-y-4 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-950">Wishlist</h2>
                  <p className="text-sm text-slate-500">Spaces you have shortlisted for later.</p>
                </div>
              </div>
              <div className="grid gap-3">
                {wishlistSpaces.map((space) => (
                  <Link
                    className="rounded-2xl border border-border bg-slate-50 px-4 py-4 transition hover:border-orange-200 hover:bg-orange-50"
                    href={`/spaces/${space.id}`}
                    key={space.id}
                  >
                    <p className="font-semibold text-slate-900">{space.name}</p>
                    <p className="mt-1 text-sm text-slate-500">
                      {space.locality ?? "Bangalore"} · {currency(space.price_per_hour)}/hr
                    </p>
                  </Link>
                ))}
                {wishlistSpaces.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border bg-slate-50 p-5 text-sm leading-7 text-slate-500">
                    Use the heart icon on any space card to save it here.
                  </div>
                ) : null}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-4 p-6">
              <h2 className="text-2xl font-semibold text-slate-950">Notification preferences</h2>
              <div className="space-y-3 text-sm text-slate-600">
                <label className="flex items-center gap-3">
                  <input defaultChecked className="h-4 w-4 accent-orange-500" type="checkbox" />
                  Booking confirmations and payment updates
                </label>
                <label className="flex items-center gap-3">
                  <input defaultChecked className="h-4 w-4 accent-orange-500" type="checkbox" />
                  New space recommendations based on your searches
                </label>
                <label className="flex items-center gap-3">
                  <input className="h-4 w-4 accent-orange-500" type="checkbox" />
                  Partner offers and special Bangalore venue promos
                </label>
              </div>

              <Button onClick={logout} type="button" variant="secondary">
                Logout
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
