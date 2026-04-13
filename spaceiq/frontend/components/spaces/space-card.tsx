"use client";

import Link from "next/link";
import Image from "next/image";
import { Heart, MapPin, Star } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { currency } from "@/lib/utils";
import { useUiStore } from "@/store/ui-store";
import type { Space } from "@/types";

export function SpaceCard({ space }: { space: Space }) {
  const toggleWishlist = useUiStore((state) => state.toggleWishlist);
  const wishlist = useUiStore((state) => state.wishlist);
  const addViewed = useUiStore((state) => state.addViewed);
  const [index, setIndex] = useState(0);

  const images = space.images?.length ? space.images : [];
  const liked = wishlist.includes(space.id);

  return (
    <motion.div whileHover={{ y: -4 }}>
      <Card className="overflow-hidden">
        <div className="relative h-52 overflow-hidden bg-gradient-to-br from-slate-200 via-slate-100 to-orange-100">
          {images.length ? (
            <Image alt={space.name} className="h-full w-full object-cover" fill src={images[index % images.length]} />
          ) : (
            <div className="flex h-full items-end bg-gradient-to-br from-slate-900/10 to-orange-500/20 p-5">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-500">{space.locality ?? "Bangalore"}</p>
                <p className="text-xl font-semibold text-slate-900">{space.name}</p>
              </div>
            </div>
          )}
          <div className="absolute left-4 top-4 flex items-center gap-2">
            <Badge>{space.type.replace("_", " ")}</Badge>
          </div>
          <button
            className={`absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full border ${
              liked ? "border-primary bg-primary text-white" : "border-white/70 bg-white/90 text-slate-700"
            }`}
            onClick={() => toggleWishlist(space.id)}
            type="button"
          >
            <Heart className={`h-4 w-4 ${liked ? "fill-current" : ""}`} />
          </button>
          {images.length > 1 ? (
            <div className="absolute bottom-4 left-4 flex gap-2">
              {images.slice(0, 4).map((_, dotIndex) => (
                <button
                  className={`h-2.5 w-2.5 rounded-full ${index === dotIndex ? "bg-white" : "bg-white/45"}`}
                  key={`${space.id}-${dotIndex}`}
                  onClick={() => setIndex(dotIndex)}
                  type="button"
                />
              ))}
            </div>
          ) : null}
        </div>

        <CardContent className="space-y-4 p-5">
          <div className="space-y-2">
            <h3 className="line-clamp-2 text-lg font-semibold text-slate-900">{space.name}</h3>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <MapPin className="h-4 w-4" />
              <span>{space.locality ?? "Bangalore"}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-amber-700">
                <Star className="h-3.5 w-3.5 fill-current" />
                {space.rating?.toFixed(1) ?? "New"}
              </span>
              <span>{space.total_reviews} reviews</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {space.amenities.slice(0, 4).map((amenity) => (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600" key={amenity}>
                {amenity}
              </span>
            ))}
            {space.amenities.length > 4 ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                +{space.amenities.length - 4} more
              </span>
            ) : null}
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">From</p>
              <p className="text-xl font-semibold text-slate-900">{currency(space.price_per_hour)}/hr</p>
            </div>
            <Link href={`/spaces/${space.id}`} onClick={() => addViewed(space.id)}>
              <Button>Book Now</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
