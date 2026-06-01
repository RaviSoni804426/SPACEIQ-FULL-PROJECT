"use client";

import { type ComponentType, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  BarChart3,
  Bot,
  BrainCircuit,
  IndianRupee,
  Percent,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";

import { apiClient } from "@/lib/api";
import type { AIAnalyticsPayload } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AiChatbot } from "@/components/ai/ai-chatbot";

const SEGMENT_COLORS = ["#1d4ed8", "#0f766e", "#d97706", "#7c3aed", "#be123c", "#334155"];

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export default function AIDashboard() {
  const [analytics, setAnalytics] = useState<AIAnalyticsPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    apiClient
      .aiAnalytics()
      .then((data) => setAnalytics(data))
      .catch(() => {/* analytics unavailable */})
      .finally(() => setIsLoading(false));
  }, []);

  const monthlyRevenue = analytics?.revenue.monthly ?? [];
  const forecast = analytics?.revenue.forecast_next_14_days ?? [];
  const byType = analytics?.segmentation.by_space_type ?? [];
  const byLocality = analytics?.segmentation.by_locality ?? [];
  const customerTiers = analytics?.segmentation.customer_tiers ?? [];
  const topKeywords = analytics?.nlp.top_keywords?.slice(0, 10) ?? [];

  const sentimentData = useMemo(() => {
    const sentiment = analytics?.nlp.review_sentiment;
    if (!sentiment) return [];
    return [
      { name: "Positive", value: sentiment.positive_pct, color: "#16a34a" },
      { name: "Neutral", value: sentiment.neutral_pct, color: "#64748b" },
      { name: "Negative", value: sentiment.negative_pct, color: "#dc2626" },
    ];
  }, [analytics]);

  const growthLabel =
    analytics?.overview.month_over_month_growth_pct === null
      ? "N/A"
      : `${analytics?.overview.month_over_month_growth_pct.toFixed(2)}%`;

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded-[28px] bg-gradient-to-r from-slate-950 via-slate-900 to-blue-900 px-6 py-7 text-white shadow-xl sm:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <BrainCircuit className="h-7 w-7 text-cyan-300" />
          <h1 className="text-3xl font-semibold tracking-tight">AI + Data Science Command Center</h1>
          <Badge className="ml-auto border-cyan-200/40 bg-cyan-200/10 text-cyan-100">
            Portfolio Edition
          </Badge>
        </div>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-200 sm:text-base">
          Forecast revenue, analyze customer segments, and run NLP sentiment analysis from booking and review data.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          title="Total Revenue"
          value={currency.format(analytics?.overview.total_revenue ?? 0)}
          subtitle="Confirmed + completed bookings"
          icon={IndianRupee}
        />
        <MetricCard
          title="Avg Booking Value"
          value={currency.format(analytics?.overview.avg_booking_value ?? 0)}
          subtitle="Revenue per successful booking"
          icon={BarChart3}
        />
        <MetricCard
          title="MoM Growth"
          value={growthLabel}
          subtitle="Monthly growth trend"
          icon={TrendingUp}
        />
        <MetricCard
          title="Cancellation Rate"
          value={`${analytics?.overview.cancellation_rate_pct.toFixed(2) ?? "0.00"}%`}
          subtitle="Share of cancelled bookings"
          icon={Percent}
        />
        <MetricCard
          title="Repeat Customer Rate"
          value={`${analytics?.overview.repeat_customer_rate_pct.toFixed(2) ?? "0.00"}%`}
          subtitle="Users with 2+ successful bookings"
          icon={Users}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-700" />
              Monthly Revenue Trend
            </CardTitle>
            <CardDescription>Revenue and booking count progression over time</CardDescription>
          </CardHeader>
          <CardContent className="h-[320px] p-4">
            {isLoading ? (
              <CenteredText text="Loading analytics..." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyRevenue}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number, key) => (key === "revenue" ? currency.format(value) : value)} />
                  <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={3} dot={{ r: 3 }} />
                  <Line yAxisId="right" type="monotone" dataKey="bookings" stroke="#f97316" strokeWidth={2} dot={{ r: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-600" />
              14-Day Revenue Forecast
            </CardTitle>
            <CardDescription>
              Model confidence: <span className="font-medium uppercase">{analytics?.overview.forecast_confidence ?? "low"}</span>
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[320px] p-4">
            {isLoading ? (
              <CenteredText text="Computing forecast..." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecast}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number) => currency.format(value)} />
                  <Area type="monotone" dataKey="upper" stroke="#cbd5e1" fill="#e2e8f0" fillOpacity={0.5} />
                  <Area type="monotone" dataKey="lower" stroke="#cbd5e1" fill="#ffffff" fillOpacity={1} />
                  <Line type="monotone" dataKey="predicted_revenue" stroke="#16a34a" strokeWidth={3} dot={{ r: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle>Revenue by Space Type</CardTitle>
            <CardDescription>Product-mix segmentation by business line</CardDescription>
          </CardHeader>
          <CardContent className="h-[290px] p-4">
            {isLoading ? (
              <CenteredText text="Loading segmentation..." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byType}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="segment" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number, key) => (key === "revenue" ? currency.format(value) : value)} />
                  <Bar dataKey="revenue" radius={[8, 8, 0, 0]}>
                    {byType.map((_, idx) => (
                      <Cell key={idx} fill={SEGMENT_COLORS[idx % SEGMENT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle>Revenue by Locality</CardTitle>
            <CardDescription>Geo-segmentation for demand concentration</CardDescription>
          </CardHeader>
          <CardContent className="h-[290px] p-4">
            {isLoading ? (
              <CenteredText text="Loading localities..." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byLocality} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="segment" width={110} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number) => currency.format(value)} />
                  <Bar dataKey="revenue" fill="#0f766e" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle>NLP Review Sentiment</CardTitle>
            <CardDescription>
              Review sample: {analytics?.nlp.review_sentiment.sample_size ?? 0} | Avg rating: {analytics?.nlp.review_sentiment.average_rating ?? 0}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid h-[320px] gap-4 p-4 sm:grid-cols-2">
            <div className="h-full">
              {isLoading ? (
                <CenteredText text="Parsing reviews..." />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={sentimentData} dataKey="value" nameKey="name" outerRadius={80} innerRadius={45} label>
                      {sentimentData.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="space-y-2 overflow-y-auto pr-2">
              <p className="text-sm font-medium text-slate-700">Top keywords</p>
              {topKeywords.length === 0 ? (
                <p className="text-sm text-slate-500">No review text available yet.</p>
              ) : (
                topKeywords.map((item) => (
                  <div key={item.keyword} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm">
                    <span className="font-medium text-slate-700">{item.keyword}</span>
                    <Badge className="border-slate-300 bg-white text-slate-700">{item.count}</Badge>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="flex flex-col border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-indigo-600" />
              AI Booking Chatbot
            </CardTitle>
            <CardDescription>Find spaces, get recommendations, and book — all from chat</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <AiChatbot fullPage />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle>Customer Tier Distribution</CardTitle>
            <CardDescription>Behavior-based segmentation for retention and growth</CardDescription>
          </CardHeader>
          <CardContent className="h-[280px] p-4">
            {isLoading ? (
              <CenteredText text="Segmenting customers..." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={customerTiers}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="segment" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="users" fill="#7c3aed" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b bg-slate-50">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-amber-500" />
              AI Recommendations
            </CardTitle>
            <CardDescription>Actionable business suggestions generated from current KPIs</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 p-4">
            {(analytics?.recommendations ?? []).map((tip, index) => (
              <div key={index} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                {tip}
              </div>
            ))}
            {!analytics?.recommendations?.length ? (
              <p className="text-sm text-slate-500">Run demo analytics seeding to generate recommendations.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: ComponentType<{ className?: string }>;
}) {
  return (
    <Card className="border-slate-200 shadow-sm">
      <CardContent className="space-y-2 p-4">
        <div className="flex items-center justify-between text-slate-500">
          <span className="text-xs font-medium uppercase tracking-wide">{title}</span>
          <Icon className="h-4 w-4" />
        </div>
        <p className="text-2xl font-semibold text-slate-900">{value}</p>
        <p className="text-xs text-slate-500">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

function CenteredText({ text }: { text: string }) {
  return <div className="flex h-full w-full items-center justify-center text-sm text-slate-500">{text}</div>;
}
