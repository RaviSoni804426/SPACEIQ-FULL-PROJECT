import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Building2,
  CalendarClock,
  CreditCard,
  MapPinned,
  Server,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const productHighlights = [
  {
    title: "Live booking lifecycle",
    description: "Users can search inventory, hold consecutive slots, pay, and track confirmed bookings in one flow.",
    icon: CalendarClock,
  },
  {
    title: "AI-assisted discovery",
    description: "SpaceBot converts natural language into structured search filters with an OpenAI fallback parser.",
    icon: BrainCircuit,
  },
  {
    title: "Partner operations",
    description: "Partners can manage their own space inventory and monitor bookings from a dedicated workflow.",
    icon: Building2,
  },
  {
    title: "Production-style integrations",
    description: "Razorpay, Google Places, and optional Redis make the system richer without breaking local development.",
    icon: ShieldCheck,
  },
];

const architectureCards = [
  {
    title: "Frontend",
    description: "Next.js App Router, Tailwind CSS, Zustand, React Query, and a polished dashboard-driven UI.",
    icon: Sparkles,
  },
  {
    title: "Backend",
    description: "FastAPI with async SQLAlchemy, route-level separation, service modules, migrations, and rate limiting.",
    icon: Server,
  },
  {
    title: "Business flows",
    description: "Search events, slot holds, payment verification, reviews, partner inventory, and analytics endpoints.",
    icon: BarChart3,
  },
];

const interviewPoints = [
  "Consecutive slot hold orchestration before payment",
  "Backend payment verification instead of frontend trust",
  "Google Places sync plus demo inventory fallback",
  "Redis acceleration with database-safe fallback behavior",
];

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-[32px] bg-slate-950 text-white shadow-2xl">
        <div className="grid gap-8 px-6 py-10 sm:px-8 lg:grid-cols-[1.08fr_0.92fr] lg:px-10 lg:py-12">
          <div className="space-y-6">
            <Badge className="border-orange-400/20 bg-orange-500/10 text-orange-200">Final Project Showcase</Badge>
            <div className="space-y-4">
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
                SpaceIQ is a full-stack booking platform you can confidently discuss in interviews.
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                It combines real product workflows like AI-assisted discovery, slot holds, Razorpay payments, partner
                inventory, and analytics into one coherent Bangalore-focused booking system.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/explore">
                <Button size="lg">
                  Explore spaces
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/ai-assistant">
                <Button size="lg" variant="secondary">
                  Try SpaceBot
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button size="lg" variant="ghost">
                  Open dashboard
                </Button>
              </Link>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {[
              {
                label: "Stack",
                value: "Next.js + FastAPI",
                description: "App Router frontend with a modular async backend.",
                icon: Server,
              },
              {
                label: "Payments",
                value: "Razorpay verified",
                description: "Backend confirmation flow with a demo fallback mode.",
                icon: CreditCard,
              },
              {
                label: "Discovery",
                value: "AI + filters",
                description: "Natural language prompts, locality search, and live inventory.",
                icon: MapPinned,
              },
              {
                label: "Operations",
                value: "Partner + analytics",
                description: "Inventory management and insight views for business users.",
                icon: BarChart3,
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
        <div className="space-y-2">
          <Badge>Why It Stands Out</Badge>
          <h2 className="text-3xl font-semibold tracking-tight text-slate-950">A stronger final-year or portfolio project than a basic CRUD app.</h2>
          <p className="max-w-3xl text-sm leading-7 text-slate-500 sm:text-base">
            SpaceIQ was shaped to be easier to present on a resume and easier to explain in technical discussion. The
            product has a clear user story, real integrations, and backend decisions worth defending.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {productHighlights.map((item) => (
            <Card key={item.title}>
              <CardContent className="space-y-4 p-6">
                <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-orange-50 text-primary">
                  <item.icon className="h-5 w-5" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-slate-950">{item.title}</h3>
                  <p className="text-sm leading-7 text-slate-500">{item.description}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.96fr_1.04fr]">
        <Card className="overflow-hidden bg-gradient-to-br from-orange-500 via-orange-400 to-amber-300 text-white">
          <CardContent className="space-y-5 p-8">
            <Badge className="border-white/20 bg-white/10 text-white">Architecture Snapshot</Badge>
            <h2 className="text-3xl font-semibold tracking-tight">Built as a real product system, not just a UI demo.</h2>
            <p className="text-sm leading-7 text-white/90">
              The active codebase is organized around a Next.js frontend and a FastAPI backend inside
              `spaceiq/backend/app`, with models, services, routers, utilities, and migrations separated cleanly.
            </p>
            <div className="grid gap-3">
              {interviewPoints.map((point) => (
                <div className="rounded-2xl border border-white/20 bg-white/12 px-4 py-3 text-sm leading-7" key={point}>
                  {point}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4">
          {architectureCards.map((item) => (
            <Card key={item.title}>
              <CardContent className="flex gap-4 p-6">
                <div className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-white">
                  <item.icon className="h-5 w-5" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-slate-950">{item.title}</h3>
                  <p className="text-sm leading-7 text-slate-500">{item.description}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
