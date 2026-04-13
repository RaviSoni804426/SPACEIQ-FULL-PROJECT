import { SearchX } from "lucide-react";

import { SpaceCard } from "@/components/spaces/space-card";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Space } from "@/types";

export function SpaceGrid({ spaces, loading }: { spaces: Space[]; loading?: boolean }) {
  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Card key={index}>
            <Skeleton className="h-52 w-full rounded-none" />
            <CardContent className="space-y-3 p-5">
              <Skeleton className="h-6 w-2/3" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-10 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (spaces.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center gap-4 py-14 text-center">
          <div className="rounded-full bg-orange-50 p-4 text-primary">
            <SearchX className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">No spaces match these filters</h3>
            <p className="text-sm text-slate-500">Try widening your budget, locality, or amenity filters.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {spaces.map((space) => (
        <SpaceCard key={space.id} space={space} />
      ))}
    </div>
  );
}
