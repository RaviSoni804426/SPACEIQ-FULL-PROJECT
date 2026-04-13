"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, UserCircle2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/explore", label: "Explore & Book" },
  { href: "/ai-assistant", label: "AI Assistant" },
  { href: "/partner", label: "Partner Hub" },
  { href: "/analytics", label: "Analytics" },
  { href: "/my-bookings", label: "My Bookings" },
  { href: "/account", label: "Account" },
];

export function Navbar() {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [open, setOpen] = useState(false);

  const initials = useMemo(() => user?.full_name?.split(" ").map((part) => part[0]).join("") ?? "", [user?.full_name]);

  return (
    <header className="sticky top-0 z-40 border-b border-white/60 bg-slate-950/92 text-white backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 text-white lg:hidden"
            onClick={() => setOpen(true)}
            type="button"
          >
            <Menu className="h-5 w-5" />
          </button>
          <Link className="flex items-center gap-2 text-lg font-semibold tracking-tight" href="/dashboard">
            <span>SpaceBook</span>
            <span className="h-2.5 w-2.5 rounded-full bg-primary" />
          </Link>
        </div>

        <nav className="hidden items-center gap-1 lg:flex">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                className={cn(
                  "rounded-full px-4 py-2 text-sm font-medium transition-colors",
                  active ? "bg-white/12 text-white" : "text-slate-300 hover:bg-white/8 hover:text-white",
                )}
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium">{user.full_name}</p>
                <p className="text-xs text-slate-400">{user.role}</p>
              </div>
              <Avatar className="h-10 w-10 border border-white/10" fallback={initials} src={user.avatar_url} />
              <Button className="hidden sm:inline-flex" onClick={logout} size="sm" variant="ghost">
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button size="sm" variant="ghost">
                  Login
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm">Get Started</Button>
              </Link>
            </>
          )}
        </div>
      </div>

      <AnimatePresence>
        {open ? (
          <>
            <motion.button
              animate={{ opacity: 1 }}
              className="fixed inset-0 z-40 bg-slate-950/70 lg:hidden"
              exit={{ opacity: 0 }}
              initial={{ opacity: 0 }}
              onClick={() => setOpen(false)}
              type="button"
            />
            <motion.aside
              animate={{ x: 0 }}
              className="fixed inset-y-0 left-0 z-50 flex w-[84%] max-w-sm flex-col gap-6 border-r border-white/10 bg-slate-950 p-6 lg:hidden"
              exit={{ x: "-100%" }}
              initial={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 240, damping: 26 }}
            >
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-lg font-semibold">
                  SpaceBook
                  <span className="h-2.5 w-2.5 rounded-full bg-primary" />
                </span>
                <button className="rounded-full p-2 text-white" onClick={() => setOpen(false)} type="button">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-3">
                {user ? (
                  <>
                    <Avatar fallback={initials} src={user.avatar_url} />
                    <div>
                      <p className="font-medium">{user.full_name}</p>
                      <p className="text-sm text-slate-400">{user.email}</p>
                    </div>
                  </>
                ) : (
                  <>
                    <UserCircle2 className="h-10 w-10 text-slate-400" />
                    <div>
                      <p className="font-medium">Guest mode</p>
                      <p className="text-sm text-slate-400">Log in to book and pay</p>
                    </div>
                  </>
                )}
              </div>

              <div className="space-y-2">
                {NAV_ITEMS.map((item) => (
                  <Link
                    className={cn(
                      "block rounded-2xl px-4 py-3 text-sm",
                      pathname === item.href || pathname.startsWith(`${item.href}/`)
                        ? "bg-white/12 text-white"
                        : "text-slate-300 hover:bg-white/8 hover:text-white",
                    )}
                    href={item.href}
                    key={item.href}
                    onClick={() => setOpen(false)}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </motion.aside>
          </>
        ) : null}
      </AnimatePresence>
    </header>
  );
}
