export function RunListSkeleton() {
  return (
    <div className="space-y-3" role="status" aria-label="Loading runs">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="card flex animate-pulse items-center justify-between"
        >
          <div className="space-y-2">
            <div className="h-4 w-56 rounded bg-ink-200" />
            <div className="h-3 w-40 rounded bg-ink-100" />
          </div>
          <div className="flex items-center gap-3">
            <div className="h-5 w-24 rounded-full bg-ink-100" />
            <div className="h-4 w-16 rounded bg-ink-100" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="card animate-pulse" role="status" aria-label="Loading">
      <div className="space-y-3">
        <div className="h-4 w-1/3 rounded bg-ink-200" />
        <div className="h-3 w-full rounded bg-ink-100" />
        <div className="h-3 w-2/3 rounded bg-ink-100" />
      </div>
    </div>
  );
}

export function TimelineSkeleton() {
  return (
    <div className="space-y-5" role="status" aria-label="Loading timeline">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex animate-pulse gap-4">
          <div className="h-3 w-3 rounded-full bg-ink-200" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-40 rounded bg-ink-200" />
            <div className="h-3 w-64 rounded bg-ink-100" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DetailSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading run detail">
      <CardSkeleton />
      <div className="grid gap-6 lg:grid-cols-2">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );
}
