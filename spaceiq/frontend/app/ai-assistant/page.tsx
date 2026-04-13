"use client";

import { MessageSquareText, Sparkles } from "lucide-react";

import { ChatPanel } from "@/components/chatbot/chat-panel";
import { Badge } from "@/components/ui/badge";

export default function AiAssistantPage() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <section className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="rounded-[28px] bg-slate-950 p-8 text-white shadow-xl">
          <Badge className="border-orange-400/20 bg-orange-500/10 text-orange-200">AI Assistant</Badge>
          <div className="mt-6 space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight">SpaceBot helps users search, shortlist, and book faster.</h1>
            <p className="text-sm leading-7 text-slate-300">
              Ask for cheap coworking near HSR, football turfs with parking, or time-based booking suggestions for
              tomorrow evening. SpaceBot uses OpenAI when configured and gracefully falls back to rule-based search.
            </p>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {[
              "Find me cheap coworking near HSR",
              "Book badminton court tomorrow 6pm",
              "Best rated spaces in Koramangala",
              "Sports venues with parking",
            ].map((prompt) => (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm leading-7 text-slate-200" key={prompt}>
                {prompt}
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-border bg-white p-5 shadow-sm">
              <Sparkles className="h-5 w-5 text-primary" />
              <h2 className="mt-4 text-lg font-semibold text-slate-900">Intent-aware responses</h2>
              <p className="mt-2 text-sm leading-7 text-slate-500">
                The assistant extracts location, time, type, budget, and amenity preferences to call the live spaces API.
              </p>
            </div>
            <div className="rounded-3xl border border-border bg-white p-5 shadow-sm">
              <MessageSquareText className="h-5 w-5 text-primary" />
              <h2 className="mt-4 text-lg font-semibold text-slate-900">Suggested spaces inline</h2>
              <p className="mt-2 text-sm leading-7 text-slate-500">
                Results return with bookable cards so users can jump straight into the booking and payment flow.
              </p>
            </div>
          </div>

          <ChatPanel className="shadow-lg" />
        </div>
      </section>
    </div>
  );
}
