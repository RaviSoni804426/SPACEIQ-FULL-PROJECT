"use client";

import { Loader2, Sparkles } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { motion } from "framer-motion";

import { SpaceCard } from "@/components/spaces/space-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useChat } from "@/hooks/use-chat";
import type { ChatTurn, Space } from "@/types";

const DEFAULT_PROMPTS = [
  "Find cheap coworking near HSR",
  "Book badminton court tomorrow 6pm",
  "Best rated spaces in Koramangala",
  "Sports venues with parking",
];

export function ChatPanel({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [message, setMessage] = useState("");
  const chat = useChat();

  const suggestedSpaces = useMemo<Space[]>(() => chat.data?.suggested_spaces ?? [], [chat.data?.suggested_spaces]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim()) return;
    const nextHistory: ChatTurn[] = [...history, { role: "user", content: message.trim() }];
    setHistory(nextHistory);
    const current = message;
    setMessage("");
    const response = await chat.mutateAsync({ message: current, history });
    setHistory([...nextHistory, { role: "assistant", content: response.reply }]);
  }

  async function runPrompt(prompt: string) {
    setMessage(prompt);
    const response = await chat.mutateAsync({ message: prompt, history });
    setHistory((current) => [
      ...current,
      { role: "user", content: prompt },
      { role: "assistant", content: response.reply },
    ]);
    setMessage("");
  }

  return (
    <Card className={className}>
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-900">SpaceBot</p>
            <p className="text-xs text-slate-500">Powered by AI for Bangalore bookings</p>
          </div>
          <Sparkles className="h-4 w-4 text-primary" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!compact ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {DEFAULT_PROMPTS.map((prompt) => (
              <button
                className="rounded-xl border border-border bg-slate-50 px-3 py-3 text-left text-sm text-slate-600 transition hover:border-orange-200 hover:bg-orange-50 hover:text-slate-900"
                key={prompt}
                onClick={() => runPrompt(prompt)}
                type="button"
              >
                {prompt}
              </button>
            ))}
          </div>
        ) : null}

        <div className={`space-y-3 overflow-y-auto rounded-2xl bg-slate-50/80 p-4 ${compact ? "h-[250px]" : "h-[360px]"}`}>
          {history.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border bg-white p-4 text-sm text-slate-500">
              Ask about coworking, football turfs, meeting rooms, pricing, or amenities.
            </div>
          ) : (
            history.map((turn, index) => (
              <motion.div
                animate={{ opacity: 1, y: 0 }}
                className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                  turn.role === "user"
                    ? "ml-auto bg-primary text-white"
                    : "bg-white text-slate-700"
                }`}
                initial={{ opacity: 0, y: 12 }}
                key={`${turn.role}-${index}`}
              >
                {turn.content}
              </motion.div>
            ))
          )}
          {chat.isPending ? (
            <div className="inline-flex items-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
              <Loader2 className="h-4 w-4 animate-spin" />
              SpaceBot is thinking...
            </div>
          ) : null}
        </div>

        {suggestedSpaces.length > 0 ? (
          <>
            <Separator />
            <div className="space-y-3">
              <p className="text-sm font-medium text-slate-700">Suggested spaces</p>
              <div className="grid gap-3">
                {suggestedSpaces.map((space) => (
                  <SpaceCard key={space.id} space={space} />
                ))}
              </div>
            </div>
          </>
        ) : null}

        <form className="flex gap-2" onSubmit={handleSubmit}>
          <Input
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Find a coworking in Indiranagar..."
            value={message}
          />
          <Button disabled={chat.isPending || !message.trim()} type="submit">
            Send
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
