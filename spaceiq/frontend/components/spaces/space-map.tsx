"use client";

import { mapEmbedUrl } from "@/lib/maps";

export function SpaceMap({
  latitude,
  longitude,
}: {
  latitude?: number | null;
  longitude?: number | null;
}) {
  return (
    <iframe
      className="h-[320px] w-full rounded-2xl border border-border"
      loading="lazy"
      referrerPolicy="no-referrer-when-downgrade"
      src={mapEmbedUrl(latitude, longitude)}
      title="Space location"
    />
  );
}
