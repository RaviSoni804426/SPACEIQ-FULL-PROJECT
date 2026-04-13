"use client";

import { Bot, X } from "lucide-react";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { ChatPanel } from "@/components/chatbot/chat-panel";

export function ChatWidget() {
  const [open, setOpen] = useState(false);

  return (
    <div className="fixed bottom-5 right-5 z-50">
      <AnimatePresence>
        {open ? (
          <motion.div
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 w-[min(92vw,380px)]"
            exit={{ opacity: 0, y: 20 }}
            initial={{ opacity: 0, y: 20 }}
          >
            <div className="mb-2 flex justify-end">
              <button
                className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-slate-950 text-white shadow-lg"
                onClick={() => setOpen(false)}
                type="button"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <ChatPanel compact />
          </motion.div>
        ) : null}
      </AnimatePresence>

      <button
        className="inline-flex h-14 w-14 animate-pulse-soft items-center justify-center rounded-full bg-primary text-white shadow-glow"
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        <Bot className="h-6 w-6" />
      </button>
    </div>
  );
}
