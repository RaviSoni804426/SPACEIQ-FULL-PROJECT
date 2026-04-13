"use client";

import { usePathname } from "next/navigation";

import { ChatWidget } from "@/components/chatbot/chat-widget";
import { Navbar } from "@/components/layout/navbar";

export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideChrome = pathname.startsWith("/login") || pathname.startsWith("/register");

  return (
    <div className="min-h-screen">
      {!hideChrome ? <Navbar /> : null}
      <main className={!hideChrome ? "pb-24" : ""}>{children}</main>
      {!hideChrome ? <ChatWidget /> : null}
    </div>
  );
}
