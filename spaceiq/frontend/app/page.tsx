import Link from "next/link";
import { ArrowRight, CalendarClock, CreditCard, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const CORE_HIGHLIGHTS = [
  {
    title: "Space Discovery",
    description: "Search by locality, type, price, and rating to quickly find the best option.",
    icon: MapPin,
  },
  {
    title: "Slot Hold Flow",
    description: "Select consecutive hourly slots and lock them for checkout.",
    icon: CalendarClock,
  },
  {
    title: "Secure Checkout",
    description: "Razorpay-backed payment verification with booking confirmation.",
    icon: CreditCard,
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <section className="rounded-[28px] bg-slate-950 px-6 py-10 text-white shadow-xl sm:px-10">
        <Badge className="border-orange-400/20 bg-orange-500/10 text-orange-200">Resume Project</Badge>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
          SpaceIQ Lite: A clean full-stack booking app for portfolio and interviews.
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
          This simplified version focuses on one strong journey: discover spaces, hold slots, pay, and track bookings.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/explore">
            <Button size="lg">
              Start Exploring
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="/my-bookings">
            <Button size="lg" variant="secondary">
              View My Bookings
            </Button>
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {CORE_HIGHLIGHTS.map((item) => (
          <Card key={item.title}>
            <CardContent className="space-y-4 p-6">
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-orange-50 text-primary">
                <item.icon className="h-5 w-5" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-semibold text-slate-950">{item.title}</h2>
                <p className="text-sm leading-7 text-slate-500">{item.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}
