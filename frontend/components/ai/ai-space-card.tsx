"use client";

import Image from "next/image";
import { MapPin, Star, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { currency } from "@/lib/utils";
import type { AIChatSpaceCard } from "@/types";

interface AiSpaceCardProps {
  space: AIChatSpaceCard;
  onBook: (space: AIChatSpaceCard) => void;
}

export function AiSpaceCard({ space, onBook }: AiSpaceCardProps) {
  return (
    <div className="flex min-w-[220px] max-w-[240px] flex-shrink-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      {/* Image */}
      <div className="relative h-32 bg-gradient-to-br from-slate-100 to-orange-100">
        {space.image_url ? (
          <Image
            alt={space.name}
            className="h-full w-full object-cover"
            fill
            src={space.image_url}
            sizes="240px"
          />
        ) : (
          <div className="flex h-full items-end bg-gradient-to-br from-slate-900/10 to-orange-400/20 p-3">
            <p className="text-sm font-semibold text-slate-900 line-clamp-2">{space.name}</p>
          </div>
        )}
        <div className="absolute left-2 top-2">
          <Badge className="text-[10px] px-2 py-0.5">{space.type.replace("_", " ")}</Badge>
        </div>
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col gap-2 p-3">
        <p className="text-sm font-semibold text-slate-900 line-clamp-2 leading-snug">{space.name}</p>

        <div className="flex items-center gap-1 text-xs text-slate-500">
          <MapPin className="h-3 w-3 flex-shrink-0" />
          <span className="truncate">{space.locality ?? "Bangalore"}</span>
        </div>

        {space.rating !== null && (
          <div className="flex items-center gap-1 text-xs text-amber-600">
            <Star className="h-3 w-3 fill-current" />
            <span>{space.rating.toFixed(1)}</span>
          </div>
        )}

        {space.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {space.amenities.slice(0, 3).map((a) => (
              <span
                key={a}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600"
              >
                {a}
              </span>
            ))}
          </div>
        )}

        <div className="mt-auto flex items-center justify-between pt-1">
          <p className="text-sm font-semibold text-slate-900">
            {currency(space.price_per_hour)}
            <span className="text-xs font-normal text-slate-400">/hr</span>
          </p>
          <Button
            size="sm"
            className="h-7 gap-1 px-3 text-xs"
            onClick={() => onBook(space)}
          >
            <Zap className="h-3 w-3" />
            Book
          </Button>
        </div>
      </div>
    </div>
  );
}
