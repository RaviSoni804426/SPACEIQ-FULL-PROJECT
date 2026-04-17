"use client";

import { GoogleMap, MarkerF, useJsApiLoader } from "@react-google-maps/api";

import { mapEmbedUrl } from "@/lib/maps";

export function SpaceMap({
  latitude,
  longitude,
}: {
  latitude?: number | null;
  longitude?: number | null;
}) {
  const { isLoaded } = useJsApiLoader({
    id: "spaceiq-map",
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY ?? "",
  });

  if (!latitude || !longitude || !process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY || !isLoaded) {
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

  return (
    <GoogleMap
      center={{ lat: latitude, lng: longitude }}
      mapContainerClassName="h-[320px] w-full rounded-2xl border border-border"
      options={{ disableDefaultUI: true, zoomControl: true }}
      zoom={15}
    >
      <MarkerF position={{ lat: latitude, lng: longitude }} />
    </GoogleMap>
  );
}
