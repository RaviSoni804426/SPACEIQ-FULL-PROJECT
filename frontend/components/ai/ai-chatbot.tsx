"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Send, Sparkles, X } from "lucide-react";
import ReactMarkdown from "react-markdown";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AiSpaceCard } from "@/components/ai/ai-space-card";
import { AiBookingModal } from "@/components/ai/ai-booking-modal";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import type { AIChatMessage, AIChatSpaceCard } from "@/types";

const SUGGESTIONS = [
  "Show me coworking spaces in Indiranagar",
  "Best meeting room under ₹500/hr",
  "Sports turf in Koramangala",
  "Budget studio in HSR Layout",
];

interface AiChatbotProps {
  /** When true, renders as a full-page panel. When false, renders as a floating widget. */
  fullPage?: boolean;
}

export function AiChatbot({ fullPage = false }: AiChatbotProps) {
  const user = useAuthStore((s) => s.user);
  const [messages, setMessages] = useState<AIChatMessage[]>([
    {
      role: "ai",
      content:
        "Hi! I'm SpaceIQ AI. I can **find spaces**, show you options, and help you **book directly** from this chat.\n\nTry asking me something like *\"Show coworking spaces in Indiranagar\"* or *\"Book a meeting room for tomorrow\"*.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [bookingTarget, setBookingTarget] = useState<AIChatSpaceCard | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isTyping) return;

    setInput("");
    const userMsg: AIChatMessage = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    // Build history for multi-turn context (last 6 turns, exclude system messages)
    const history = messages
      .filter((m) => m.role !== "system")
      .slice(-6)
      .map((m) => ({ role: m.role === "ai" ? "assistant" : "user", content: m.content }));

    try {
      const data = await apiClient.aiChat(trimmed, history);

      const aiMsg: AIChatMessage = {
        role: "ai",
        content: data.reply || "I didn't get a response. Please try again.",
        action: data.action,
        spaces: data.spaces,
        book_space_id: data.book_space_id,
      };
      setMessages((prev) => [...prev, aiMsg]);

      // If AI wants to directly open booking for a specific space
      if (data.action === "book_space" && data.book_space_id) {
        const target = data.spaces?.find((s) => s.id === data.book_space_id) ?? data.spaces?.[0];
        if (target) setBookingTarget(target);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `Request failed: ${err?.detail ?? "connection error"}. Please try again.`,
        },
      ]);
    } finally {
      setIsTyping(false);
      inputRef.current?.focus();
    }
  }

  function handleBooked(bookingId: string, spaceName: string) {
    setBookingTarget(null);
    setMessages((prev) => [
      ...prev,
      {
        role: "ai",
        content: `✅ **Booking confirmed** for **${spaceName}**!\n\nYour booking ID is \`${bookingId}\`. You can view it in [My Bookings](/my-bookings).`,
      },
    ]);
  }

  const containerClass = fullPage
    ? "flex h-full flex-col"
    : "flex h-[600px] flex-col rounded-[28px] border border-slate-200 bg-white shadow-lg overflow-hidden";

  return (
    <>
      <div className={containerClass}>
        {/* Header */}
        {!fullPage && (
          <div className="flex items-center gap-3 border-b bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-4 text-white">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold">SpaceIQ AI</p>
              <p className="text-xs text-indigo-200">Find & book spaces instantly</p>
            </div>
            <div className="ml-auto flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-1 text-xs">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" />
              Online
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              message={msg}
              onBook={(space) => setBookingTarget(space)}
            />
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3 text-sm text-slate-500">
                <span className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:0ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:150ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:300ms]" />
                </span>
                AI is thinking…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Suggestions (only when just the welcome message is shown) */}
        {messages.length === 1 && (
          <div className="border-t bg-slate-50 px-4 py-3">
            <p className="mb-2 text-xs font-medium uppercase tracking-widest text-slate-400">Try asking</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  type="button"
                  className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t bg-white px-4 py-3">
          {!user && (
            <p className="mb-2 text-center text-xs text-slate-500">
              <a href="/login" className="font-medium text-indigo-600 hover:underline">Log in</a> to book spaces directly from chat.
            </p>
          )}
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
          >
            <Input
              ref={inputRef}
              placeholder="Ask me to find or book a space…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 rounded-xl"
              disabled={isTyping}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isTyping}
              className="h-10 w-10 flex-shrink-0 rounded-xl bg-indigo-600 hover:bg-indigo-700"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>

      {/* Booking modal */}
      {bookingTarget && (
        <AiBookingModal
          space={bookingTarget}
          onClose={() => setBookingTarget(null)}
          onBooked={handleBooked}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Message bubble
// ---------------------------------------------------------------------------

function MessageBubble({
  message,
  onBook,
}: {
  message: AIChatMessage;
  onBook: (space: AIChatSpaceCard) => void;
}) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <p className="rounded-full bg-red-50 px-4 py-1.5 text-xs text-red-600">{message.content}</p>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} gap-2`}>
      {!isUser && (
        <div className="mt-1 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100">
          <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
        </div>
      )}

      <div className={`flex max-w-[85%] flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
        {/* Text bubble */}
        <div
          className={[
            "rounded-2xl px-4 py-3 text-sm leading-6",
            isUser
              ? "rounded-tr-sm bg-indigo-600 text-white"
              : "rounded-tl-sm bg-slate-100 text-slate-900",
          ].join(" ")}
        >
          <MarkdownContent content={message.content} isUser={isUser} />
        </div>

        {/* Space cards carousel */}
        {!isUser && message.action === "show_spaces" && message.spaces && message.spaces.length > 0 && (
          <div className="flex gap-3 overflow-x-auto pb-1 max-w-full">
            {message.spaces.map((space) => (
              <AiSpaceCard key={space.id} space={space} onBook={onBook} />
            ))}
          </div>
        )}

        {/* Single book_space action */}
        {!isUser && message.action === "book_space" && message.book_space_id && message.spaces && message.spaces.length > 0 && (
          <div className="flex gap-3 overflow-x-auto pb-1 max-w-full">
            {message.spaces.map((space) => (
              <AiSpaceCard key={space.id} space={space} onBook={onBook} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MarkdownContent({ content, isUser }: { content: string; isUser: boolean }) {
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
        strong: ({ children }) => (
          <strong className={isUser ? "font-semibold text-white" : "font-semibold text-slate-900"}>
            {children}
          </strong>
        ),
        em: ({ children }) => <em className="italic">{children}</em>,
        ul: ({ children }) => <ul className="ml-4 list-disc space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="ml-4 list-decimal space-y-1">{children}</ol>,
        li: ({ children }) => <li>{children}</li>,
        code: ({ children }) => (
          <code className={`rounded px-1 py-0.5 font-mono text-xs ${isUser ? "bg-white/20" : "bg-slate-200"}`}>
            {children}
          </code>
        ),
        a: ({ href, children }) => (
          <a href={href} className="underline hover:opacity-80" target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
