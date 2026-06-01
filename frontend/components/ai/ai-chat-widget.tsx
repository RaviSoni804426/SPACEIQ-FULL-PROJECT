"use client";

import { useRouter } from "next/navigation";
import { Bot } from "lucide-react";
import { motion } from "framer-motion";

export function AiChatWidget() {
  const router = useRouter();

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => router.push("/chat")}
        type="button"
        aria-label="Open AI chat"
        className="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-500/30 transition-shadow hover:shadow-xl hover:shadow-indigo-500/40"
      >
        <Bot className="h-6 w-6" />
        {/* Pulse ring */}
        <span className="absolute inset-0 rounded-full animate-ping bg-indigo-400 opacity-20" />
      </motion.button>
    </div>
  );
}
