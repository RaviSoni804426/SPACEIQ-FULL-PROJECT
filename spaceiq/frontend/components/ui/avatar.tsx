import Image from "next/image";
import { User2 } from "lucide-react";

import { cn } from "@/lib/utils";

export function Avatar({
  src,
  fallback,
  className,
}: {
  src?: string | null;
  fallback?: string;
  className?: string;
}) {
  if (src) {
    return <Image alt={fallback ?? "Avatar"} className={cn("h-10 w-10 rounded-full object-cover", className)} height={40} src={src} width={40} />;
  }
  return (
    <div className={cn("flex h-10 w-10 items-center justify-center rounded-full bg-slate-200 text-slate-600", className)}>
      {fallback ? fallback.slice(0, 2).toUpperCase() : <User2 className="h-4 w-4" />}
    </div>
  );
}
