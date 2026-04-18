"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useLogin } from "@/hooks/use-auth";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginValues = z.infer<typeof loginSchema>;

function getErrorDetail(error: unknown) {
  if (error && typeof error === "object" && "detail" in error && typeof error.detail === "string") {
    return error.detail;
  }
  return "Login failed. Please try again.";
}

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  async function onSubmit(values: LoginValues) {
    try {
      await login.mutateAsync(values);
      toast.success("Welcome back to SpaceIQ.");
      router.push("/explore");
    } catch (error) {
      toast.error(getErrorDetail(error));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-[28px] border border-white/60 bg-white shadow-xl lg:grid-cols-[1.05fr_0.95fr]">
        <section className="hidden bg-slate-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="space-y-5">
            <div className="inline-flex items-center gap-2 text-lg font-semibold">
              <span>SpaceIQ</span>
              <span className="h-2.5 w-2.5 rounded-full bg-primary" />
            </div>
            <div className="space-y-3">
              <h1 className="max-w-md text-4xl font-semibold leading-tight">
                Bangalore spaces for deep work, pickup games, and quick meetings.
              </h1>
              <p className="max-w-md text-sm leading-7 text-slate-300">
                Sign in to manage bookings, pay through Razorpay, and get AI-powered suggestions tailored to your
                locality, budget, and timing.
              </p>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { label: "Coworking", value: "HSR, Koramangala, Indiranagar" },
              { label: "Sports", value: "Football, badminton, box cricket" },
              { label: "Payments", value: "Real Razorpay checkout flow" },
            ].map((item) => (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4" key={item.label}>
                <p className="text-sm font-medium text-white">{item.label}</p>
                <p className="mt-2 text-xs leading-6 text-slate-300">{item.value}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="flex items-center justify-center bg-white p-6 sm:p-10">
          <Card className="w-full max-w-md border-none shadow-none">
            <CardContent className="space-y-8 p-0">
              <div className="space-y-2">
                <p className="text-sm font-medium uppercase tracking-[0.24em] text-primary">Login</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Access your SpaceIQ account</h2>
                <p className="text-sm leading-7 text-slate-500">
                  Use your email and password to continue to exploration and bookings.
                </p>
              </div>

              <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700" htmlFor="email">
                    Email
                  </label>
                  <Input id="email" placeholder="you@company.com" type="email" {...register("email")} />
                  {errors.email ? <p className="text-sm text-red-500">{errors.email.message}</p> : null}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700" htmlFor="password">
                    Password
                  </label>
                  <Input id="password" placeholder="Enter your password" type="password" {...register("password")} />
                  {errors.password ? <p className="text-sm text-red-500">{errors.password.message}</p> : null}
                </div>

                <Button className="w-full" disabled={login.isPending} size="lg" type="submit">
                  {login.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Sign in
                </Button>
              </form>

              <p className="text-sm text-slate-500">
                New to SpaceIQ?{" "}
                <Link className="font-medium text-primary hover:text-orange-500" href="/register">
                  Create an account
                </Link>
              </p>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
