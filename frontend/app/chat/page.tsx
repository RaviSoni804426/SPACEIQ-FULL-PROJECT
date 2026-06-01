"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Bot, Send, Sparkles, MapPin, Star, Zap, Clock3,
  CheckCircle2, Loader2, CalendarDays, ArrowLeft,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { useSpace } from "@/hooks/use-spaces";
import { useHoldBooking } from "@/hooks/use-bookings";
import { useInitPayment, useVerifyPayment } from "@/hooks/use-bookings";
import { loadRazorpayScript } from "@/lib/razorpay";
import { currency, formatTime } from "@/lib/utils";
import type { AIChatSpaceCard, AIChatMessage, TimeSlot } from "@/types";

// ─── Types ────────────────────────────────────────────────────────────────────

type BookingStep =
  | { type: "idle" }
  | { type: "pick_date"; space: AIChatSpaceCard }
  | { type: "pick_slots"; space: AIChatSpaceCard; date: string }
  | { type: "confirm"; space: AIChatSpaceCard; date: string; slots: TimeSlot[]; holdId: string; expiresAt: string; total: number }
  | { type: "done"; bookingId: string; spaceName: string; date: string; timeRange: string };

const SUGGESTIONS = [
  "Show coworking spaces in Indiranagar",
  "Meeting room under ₹500/hr",
  "Sports turf in Koramangala",
  "Budget studio in HSR Layout",
  "Best rated space in Whitefield",
];

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const user = useAuthStore((s) => s.user);
  const [messages, setMessages] = useState<AIChatMessage[]>([
    {
      role: "ai",
      content: user
        ? `Hey ${user.full_name.split(" ")[0]}! 👋 I'm SpaceIQ AI.\n\nTell me what you need — I'll find the right space and walk you through booking it right here in chat.`
        : "Hey! 👋 I'm SpaceIQ AI.\n\nI can find spaces and help you book them. **Log in** to complete a booking, or just browse for now.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [bookingStep, setBookingStep] = useState<BookingStep>({ type: "idle" });
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping, bookingStep]);

  const pushAiMessage = useCallback((content: string, extra?: Partial<AIChatMessage>) => {
    setMessages((prev) => [...prev, { role: "ai", content, ...extra }]);
  }, []);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isTyping) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setIsTyping(true);

    const history = messages
      .filter((m) => m.role !== "system")
      .slice(-8)
      .map((m) => ({ role: m.role === "ai" ? "assistant" : "user", content: m.content }));

    try {
      const data = await apiClient.aiChat(trimmed, history);
      const aiMsg: AIChatMessage = {
        role: "ai",
        content: data.reply || "Sorry, I didn't get a response.",
        action: data.action,
        spaces: data.spaces,
        book_space_id: data.book_space_id,
      };
      setMessages((prev) => [...prev, aiMsg]);

      if (data.action === "book_space" && data.spaces?.length) {
        const target = data.spaces.find((s) => s.id === data.book_space_id) ?? data.spaces[0];
        startBooking(target);
      }
    } catch (err: any) {
      setMessages((prev) => [...prev, {
        role: "system",
        content: `Connection error: ${err?.detail ?? "please try again."}`,
      }]);
    } finally {
      setIsTyping(false);
      inputRef.current?.focus();
    }
  }

  function startBooking(space: AIChatSpaceCard) {
    setBookingStep({ type: "pick_date", space });
    pushAiMessage(`Great choice! **${space.name}** is ₹${space.price_per_hour}/hr.\n\nPick a date below to see available slots.`);
  }

  function handleDateChosen(space: AIChatSpaceCard, date: string) {
    setBookingStep({ type: "pick_slots", space, date });
    setMessages((prev) => [...prev, { role: "user", content: `Date: ${date}` }]);
    pushAiMessage(`Loading slots for **${date}**…`);
  }

  function handleSlotsChosen(space: AIChatSpaceCard, date: string, slots: TimeSlot[], holdId: string, expiresAt: string, total: number) {
    const timeRange = `${formatTime(slots[0].start_time)} – ${formatTime(slots[slots.length - 1].end_time)}`;
    setBookingStep({ type: "confirm", space, date, slots, holdId, expiresAt, total });
    setMessages((prev) => [...prev, { role: "user", content: `Slots: ${timeRange}` }]);
    pushAiMessage(`Slots held ✅\n\n**${space.name}** · ${date} · ${timeRange}\n**Total: ${currency(total)}**\n\nPay below to confirm your booking.`);
  }

  function handleBooked(bookingId: string, spaceName: string, date: string, timeRange: string) {
    setBookingStep({ type: "done", bookingId, spaceName, date, timeRange });
    pushAiMessage(`🎉 **Booking confirmed!**\n\n**${spaceName}** on ${date} · ${timeRange}\nBooking ID: \`${bookingId}\`\n\nAnything else I can help with?`);
  }

  function cancelBooking() {
    setBookingStep({ type: "idle" });
    pushAiMessage("No problem! Let me know if you want to look at other spaces.");
  }

  return (
    <div className="flex h-[calc(100vh-65px)] flex-col bg-slate-50">
      {/* Top bar */}
      <div className="flex items-center gap-3 border-b bg-white px-4 py-3 shadow-sm">
        <Link href="/" className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 text-slate-500 hover:bg-slate-50">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600">
          <Bot className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">SpaceIQ AI</p>
          <p className="text-xs text-slate-500">Find spaces · Book instantly</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Online
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-5">
          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              message={msg}
              onBook={startBooking}
            />
          ))}

          {/* Inline booking steps */}
          {bookingStep.type === "pick_date" && (
            <DatePickerStep
              space={bookingStep.space}
              onConfirm={(date) => handleDateChosen(bookingStep.space, date)}
              onCancel={cancelBooking}
            />
          )}
          {bookingStep.type === "pick_slots" && (
            <SlotPickerStep
              space={bookingStep.space}
              date={bookingStep.date}
              onConfirm={(slots, holdId, expiresAt, total) =>
                handleSlotsChosen(bookingStep.space, bookingStep.date, slots, holdId, expiresAt, total)
              }
              onCancel={cancelBooking}
            />
          )}
          {bookingStep.type === "confirm" && (
            <PaymentStep
              space={bookingStep.space}
              date={bookingStep.date}
              slots={bookingStep.slots}
              holdId={bookingStep.holdId}
              expiresAt={bookingStep.expiresAt}
              total={bookingStep.total}
              onSuccess={(id) => {
                const tr = `${formatTime(bookingStep.slots[0].start_time)} – ${formatTime(bookingStep.slots[bookingStep.slots.length - 1].end_time)}`;
                handleBooked(id, bookingStep.space.name, bookingStep.date, tr);
              }}
              onCancel={cancelBooking}
            />
          )}
          {bookingStep.type === "done" && (
            <BookingDoneStep
              bookingId={bookingStep.bookingId}
              spaceName={bookingStep.spaceName}
              date={bookingStep.date}
              timeRange={bookingStep.timeRange}
              onReset={() => setBookingStep({ type: "idle" })}
            />
          )}

          {isTyping && (
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100">
                <Sparkles className="h-4 w-4 text-indigo-600" />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm bg-white px-4 py-3 shadow-sm">
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:0ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:120ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:240ms]" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Suggestions strip */}
      {messages.length === 1 && bookingStep.type === "idle" && (
        <div className="border-t bg-white px-4 py-3">
          <p className="mb-2 text-xs font-medium uppercase tracking-widest text-slate-400">Try asking</p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => sendMessage(s)}
                type="button"
                className="flex-shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input bar */}
      <div className="border-t bg-white px-4 py-3">
        {!user && (
          <p className="mb-2 text-center text-xs text-slate-500">
            <Link href="/login" className="font-medium text-indigo-600 hover:underline">Log in</Link> to book spaces directly from chat.
          </p>
        )}
        <form
          className="mx-auto flex max-w-2xl items-center gap-2"
          onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
        >
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
            placeholder="Ask me to find or book a space…"
            className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── Message Bubble ───────────────────────────────────────────────────────────

function MessageBubble({ message, onBook }: { message: AIChatMessage; onBook: (s: AIChatSpaceCard) => void }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <p className="rounded-full bg-red-50 px-4 py-1.5 text-xs text-red-600">{message.content}</p>
      </div>
    );
  }

  const showCards =
    !isUser &&
    (message.action === "show_spaces" || message.action === "book_space") &&
    message.spaces &&
    message.spaces.length > 0;

  return (
    <div className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-100">
          <Sparkles className="h-4 w-4 text-indigo-600" />
        </div>
      )}
      <div className={`flex max-w-[80%] flex-col gap-3 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={[
            "rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm",
            isUser
              ? "rounded-tr-sm bg-indigo-600 text-white"
              : "rounded-tl-sm bg-white text-slate-900",
          ].join(" ")}
        >
          <MdText content={message.content} isUser={isUser} />
        </div>
        {showCards && (
          <div className="grid w-full gap-3 sm:grid-cols-2">
            {message.spaces!.map((space) => (
              <SpaceResultCard key={space.id} space={space} onBook={onBook} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MdText({ content, isUser }: { content: string; isUser: boolean }) {
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        ul: ({ children }) => <ul className="ml-4 list-disc space-y-0.5">{children}</ul>,
        li: ({ children }) => <li>{children}</li>,
        code: ({ children }) => (
          <code className={`rounded px-1 py-0.5 font-mono text-xs ${isUser ? "bg-white/20" : "bg-slate-100"}`}>
            {children}
          </code>
        ),
        a: ({ href, children }) => (
          <a href={href} className="underline hover:opacity-80">{children}</a>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

// ─── Space Result Card ────────────────────────────────────────────────────────

function SpaceResultCard({ space, onBook }: { space: AIChatSpaceCard; onBook: (s: AIChatSpaceCard) => void }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="relative h-36 bg-gradient-to-br from-slate-100 to-orange-100">
        {space.image_url ? (
          <Image alt={space.name} fill src={space.image_url} className="object-cover" sizes="400px" />
        ) : (
          <div className="flex h-full items-end bg-gradient-to-br from-slate-900/10 to-orange-400/20 p-3">
            <p className="text-sm font-semibold text-slate-900">{space.name}</p>
          </div>
        )}
        <div className="absolute left-2 top-2">
          <Badge className="text-[10px] px-2 py-0.5 capitalize">{space.type.replace("_", " ")}</Badge>
        </div>
      </div>
      <div className="p-3 space-y-2">
        <p className="font-semibold text-slate-900 text-sm leading-snug line-clamp-1">{space.name}</p>
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{space.locality ?? "Bangalore"}</span>
          {space.rating && (
            <span className="flex items-center gap-1 text-amber-600"><Star className="h-3 w-3 fill-current" />{space.rating.toFixed(1)}</span>
          )}
        </div>
        {space.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {space.amenities.slice(0, 3).map((a) => (
              <span key={a} className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">{a}</span>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between pt-1">
          <p className="text-sm font-bold text-slate-900">{currency(space.price_per_hour)}<span className="text-xs font-normal text-slate-400">/hr</span></p>
          <button
            onClick={() => onBook(space)}
            type="button"
            className="flex items-center gap-1 rounded-xl bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 transition"
          >
            <Zap className="h-3 w-3" /> Book Now
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Step 1: Date Picker ──────────────────────────────────────────────────────

function DatePickerStep({ space, onConfirm, onCancel }: {
  space: AIChatSpaceCard;
  onConfirm: (date: string) => void;
  onCancel: () => void;
}) {
  const today = new Date().toISOString().split("T")[0];
  const [date, setDate] = useState(today);

  return (
    <div className="ml-11 rounded-2xl border border-indigo-100 bg-indigo-50 p-4 space-y-3">
      <p className="text-sm font-semibold text-indigo-900 flex items-center gap-2">
        <CalendarDays className="h-4 w-4" /> Choose a date for {space.name}
      </p>
      <input
        type="date"
        min={today}
        value={date}
        onChange={(e) => setDate(e.target.value)}
        className="flex h-10 w-full rounded-xl border border-indigo-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
      />
      <div className="flex gap-2">
        <button
          onClick={() => onConfirm(date)}
          type="button"
          className="flex-1 rounded-xl bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
        >
          See Available Slots →
        </button>
        <button onClick={onCancel} type="button" className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 transition">
          Cancel
        </button>
      </div>
    </div>
  );
}

// ─── Step 2: Slot Picker ──────────────────────────────────────────────────────

function SlotPickerStep({ space, date, onConfirm, onCancel }: {
  space: AIChatSpaceCard;
  date: string;
  onConfirm: (slots: TimeSlot[], holdId: string, expiresAt: string, total: number) => void;
  onCancel: () => void;
}) {
  const spaceQuery = useSpace(space.id, date);
  const holdBooking = useHoldBooking();
  const user = useAuthStore((s) => s.user);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const slots = spaceQuery.data?.available_slots ?? [];
  const pricePerHour = Number(spaceQuery.data?.price_per_hour ?? space.price_per_hour);

  function toggleSlot(slotId: string) {
    const order = new Map(slots.map((s, i) => [s.id, i]));
    setSelectedIds((cur) => {
      if (cur.includes(slotId)) return cur.filter((id) => id !== slotId);
      const next = [...cur, slotId].sort((a, b) => (order.get(a) ?? 0) - (order.get(b) ?? 0));
      const idxs = next.map((id) => order.get(id) ?? 0);
      if (!idxs.every((v, i) => i === 0 || v - idxs[i - 1] === 1)) {
        toast.error("Select consecutive slots only.");
        return cur;
      }
      return next;
    });
  }

  async function handleHold() {
    if (!user) { toast.error("Please log in to book."); return; }
    if (!selectedIds.length) { toast.error("Select at least one slot."); return; }
    try {
      const res = await holdBooking.mutateAsync({ space_id: space.id, date, slot_ids: selectedIds });
      const selectedSlots = slots.filter((s) => selectedIds.includes(s.id));
      onConfirm(selectedSlots, res.hold_id, res.expires_at, res.total_amount);
    } catch (err: any) {
      toast.error(err?.detail ?? "Could not hold slots. Try again.");
    }
  }

  const selectedSlots = slots.filter((s) => selectedIds.includes(s.id));
  const total = selectedSlots.length * pricePerHour;

  return (
    <div className="ml-11 rounded-2xl border border-indigo-100 bg-indigo-50 p-4 space-y-3">
      <p className="text-sm font-semibold text-indigo-900">
        Available slots for <span className="text-indigo-700">{date}</span>
      </p>

      {spaceQuery.isLoading ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading slots…
        </div>
      ) : slots.length === 0 ? (
        <p className="text-sm text-slate-500">No slots available for this date. Try another date.</p>
      ) : (
        <div className="grid grid-cols-4 gap-2 sm:grid-cols-5">
          {slots.map((slot) => {
            const sel = selectedIds.includes(slot.id);
            const booked = slot.status === "booked";
            const held = slot.status === "held";
            return (
              <button
                key={slot.id}
                disabled={booked || held}
                onClick={() => toggleSlot(slot.id)}
                type="button"
                className={[
                  "rounded-xl border py-2 text-xs font-medium transition",
                  sel ? "border-indigo-500 bg-indigo-600 text-white"
                    : booked ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 line-through"
                    : held ? "cursor-not-allowed border-amber-200 bg-amber-50 text-amber-600"
                    : "border-slate-200 bg-white text-slate-700 hover:border-indigo-300 hover:bg-indigo-50",
                ].join(" ")}
              >
                {formatTime(slot.start_time)}
              </button>
            );
          })}
        </div>
      )}

      {selectedSlots.length > 0 && (
        <div className="rounded-xl bg-white px-3 py-2 text-xs text-slate-600 flex items-center justify-between">
          <span>{selectedSlots.length} slot{selectedSlots.length > 1 ? "s" : ""} · {formatTime(selectedSlots[0].start_time)} – {formatTime(selectedSlots[selectedSlots.length - 1].end_time)}</span>
          <span className="font-bold text-slate-900">{currency(total)}</span>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleHold}
          disabled={holdBooking.isPending || selectedIds.length === 0}
          type="button"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition disabled:opacity-40"
        >
          {holdBooking.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Hold & Continue →
        </button>
        <button onClick={onCancel} type="button" className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 transition">
          Cancel
        </button>
      </div>
    </div>
  );
}

// ─── Step 3: Payment ──────────────────────────────────────────────────────────

function PaymentStep({ space, date, slots, holdId, expiresAt, total, onSuccess, onCancel }: {
  space: AIChatSpaceCard;
  date: string;
  slots: TimeSlot[];
  holdId: string;
  expiresAt: string;
  total: number;
  onSuccess: (bookingId: string) => void;
  onCancel: () => void;
}) {
  const user = useAuthStore((s) => s.user);
  const initPayment = useInitPayment();
  const verifyPayment = useVerifyPayment();
  const [paying, setPaying] = useState(false);
  const [remainingSecs, setRemainingSecs] = useState(0);

  useEffect(() => {
    const tick = () => {
      const diff = Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000));
      setRemainingSecs(diff);
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [expiresAt]);

  const timeRange = `${formatTime(slots[0].start_time)} – ${formatTime(slots[slots.length - 1].end_time)}`;
  const mm = String(Math.floor(remainingSecs / 60)).padStart(2, "0");
  const ss = String(remainingSecs % 60).padStart(2, "0");

  async function handlePay() {
    setPaying(true);
    try {
      const init = await initPayment.mutateAsync(holdId);
      if (init.mode === "demo") {
        const payId = `pay_demo_${Date.now()}`;
        const booking = await verifyPayment.mutateAsync({
          hold_id: holdId,
          razorpay_order_id: init.order_id,
          razorpay_payment_id: payId,
          razorpay_signature: "demo_signature",
        });
        toast.success("Demo payment confirmed!");
        onSuccess(booking.id);
        return;
      }
      const loaded = await loadRazorpayScript();
      if (!loaded || !window.Razorpay) { toast.error("Razorpay could not load."); return; }
      const rp = new window.Razorpay({
        key: init.key_id,
        amount: init.amount,
        currency: init.currency,
        order_id: init.order_id,
        name: "SpaceIQ",
        description: space.name,
        prefill: { name: user?.full_name ?? "", email: user?.email ?? "", contact: user?.phone ?? "" },
        handler: async (res: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) => {
          const booking = await verifyPayment.mutateAsync({
            hold_id: holdId,
            razorpay_order_id: res.razorpay_order_id,
            razorpay_payment_id: res.razorpay_payment_id,
            razorpay_signature: res.razorpay_signature,
          });
          toast.success("Payment verified!");
          onSuccess(booking.id);
        },
        theme: { color: "#4f46e5" },
      });
      rp.open();
    } catch (err: any) {
      toast.error(err?.detail ?? "Payment failed. Try again.");
    } finally {
      setPaying(false);
    }
  }

  return (
    <div className="ml-11 rounded-2xl border border-emerald-100 bg-emerald-50 p-4 space-y-3">
      <p className="text-sm font-semibold text-emerald-900">Confirm & Pay</p>
      <div className="rounded-xl bg-white p-3 space-y-1.5 text-sm">
        <div className="flex justify-between text-slate-600"><span>Space</span><span className="font-medium text-slate-900 text-right max-w-[180px] truncate">{space.name}</span></div>
        <div className="flex justify-between text-slate-600"><span>Date</span><span className="font-medium text-slate-900">{date}</span></div>
        <div className="flex justify-between text-slate-600"><span>Time</span><span className="font-medium text-slate-900">{timeRange}</span></div>
        <div className="flex justify-between text-slate-600 border-t pt-1.5 mt-1.5"><span className="font-semibold">Total</span><span className="font-bold text-slate-900 text-base">{currency(total)}</span></div>
      </div>
      {remainingSecs > 0 && (
        <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          <Clock3 className="h-3.5 w-3.5 flex-shrink-0" />
          Hold expires in <span className="font-bold tabular-nums ml-1">{mm}:{ss}</span>
        </div>
      )}
      <div className="flex gap-2">
        <button
          onClick={handlePay}
          disabled={paying || remainingSecs === 0}
          type="button"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 transition disabled:opacity-40"
        >
          {paying && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Pay {currency(total)} & Confirm
        </button>
        <button onClick={onCancel} type="button" className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 transition">
          Cancel
        </button>
      </div>
    </div>
  );
}

// ─── Step 4: Done ─────────────────────────────────────────────────────────────

function BookingDoneStep({ bookingId, spaceName, date, timeRange, onReset }: {
  bookingId: string;
  spaceName: string;
  date: string;
  timeRange: string;
  onReset: () => void;
}) {
  return (
    <div className="ml-11 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-emerald-500">
          <CheckCircle2 className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="font-semibold text-emerald-900">Booking Confirmed!</p>
          <p className="text-xs text-emerald-700">{spaceName} · {date} · {timeRange}</p>
        </div>
      </div>
      <div className="rounded-xl bg-white px-3 py-2 text-xs text-slate-500">
        Booking ID: <span className="font-mono text-slate-800">{bookingId}</span>
      </div>
      <div className="flex gap-2">
        <Link href="/my-bookings" className="flex-1 rounded-xl bg-emerald-600 py-2 text-center text-sm font-semibold text-white hover:bg-emerald-700 transition">
          View My Bookings
        </Link>
        <button onClick={onReset} type="button" className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 transition">
          Book Another
        </button>
      </div>
    </div>
  );
}
