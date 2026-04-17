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
import { GoogleSignInButton } from "@/components/auth/google-sign-in-button";
import { useRegister } from "@/hooks/use-auth";

const registerSchema = z.object({
  full_name: z.string().min(2, "Enter your full name"),
  email: z.string().email("Enter a valid email"),
  phone: z.string().min(10, "Enter a valid phone number").optional().or(z.literal("")),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Include at least one uppercase letter")
    .regex(/[0-9]/, "Include at least one number"),
});

type RegisterValues = z.infer<typeof registerSchema>;

function getErrorDetail(error: unknown) {
  if (error && typeof error === "object" && "detail" in error && typeof error.detail === "string") {
    return error.detail;
  }
  return "Registration failed. Please try again.";
}

export default function RegisterPage() {
  const router = useRouter();
  const registerUser = useRegister();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      phone: "",
      password: "",
    },
  });

  async function onSubmit(values: RegisterValues) {
    try {
      await registerUser.mutateAsync({
        ...values,
        phone: values.phone || undefined,
      });
      toast.success("Account created. You are ready to start booking.");
      router.push("/dashboard");
    } catch (error) {
      toast.error(getErrorDetail(error));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="grid w-full max-w-6xl overflow-hidden rounded-[28px] border border-white/60 bg-white shadow-xl lg:grid-cols-[0.96fr_1.04fr]">
        <section className="flex items-center justify-center bg-white p-6 sm:p-10">
          <Card className="w-full max-w-md border-none shadow-none">
            <CardContent className="space-y-8 p-0">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 text-sm font-medium uppercase tracking-[0.24em] text-primary">
                  <span>Create Account</span>
                  <span className="h-2 w-2 rounded-full bg-primary" />
                </div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Start discovering spaces in Bangalore</h1>
                <p className="text-sm leading-7 text-slate-500">
                  Join as a user today. You can switch to a partner workflow later if you want to list spaces.
                </p>
              </div>

              <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700" htmlFor="full_name">
                    Full name
                  </label>
                  <Input id="full_name" placeholder="Aarav Nair" {...register("full_name")} />
                  {errors.full_name ? <p className="text-sm text-red-500">{errors.full_name.message}</p> : null}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700" htmlFor="email">
                    Email
                  </label>
                  <Input id="email" placeholder="you@company.com" type="email" {...register("email")} />
                  {errors.email ? <p className="text-sm text-red-500">{errors.email.message}</p> : null}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700" htmlFor="phone">
                    Phone
                  </label>
                  <Input id="phone" placeholder="9876543210" {...register("phone")} />
                  {errors.phone ? <p className="text-sm text-red-500">{errors.phone.message}</p> : null}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700" htmlFor="password">
                    Password
                  </label>
                  <Input id="password" placeholder="Create a secure password" type="password" {...register("password")} />
                  {errors.password ? <p className="text-sm text-red-500">{errors.password.message}</p> : null}
                </div>

                <Button className="w-full" disabled={registerUser.isPending} size="lg" type="submit">
                  {registerUser.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Create account
                </Button>
              </form>

              <GoogleSignInButton mode="signup" />

              <p className="text-sm text-slate-500">
                Already have an account?{" "}
                <Link className="font-medium text-primary hover:text-orange-500" href="/login">
                  Sign in
                </Link>
              </p>
            </CardContent>
          </Card>
        </section>

        <section className="hidden bg-gradient-to-br from-orange-500 via-orange-400 to-amber-300 p-10 text-white lg:block">
          <div className="space-y-8">
            <div className="space-y-3">
              <p className="text-sm font-medium uppercase tracking-[0.24em] text-white/80">Why SpaceIQ</p>
              <h2 className="max-w-md text-4xl font-semibold leading-tight">One place to find coworking, courts, studios, and meeting rooms.</h2>
            </div>

            <div className="grid gap-4">
              {[
                "Search by locality, budget, rating, amenities, and date.",
                "Hold slots for five minutes so users do not lose availability at checkout.",
                "Use SpaceBot for fast recommendations across Bangalore neighborhoods.",
              ].map((point) => (
                <div className="rounded-2xl border border-white/20 bg-white/10 p-4 text-sm leading-7" key={point}>
                  {point}
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
