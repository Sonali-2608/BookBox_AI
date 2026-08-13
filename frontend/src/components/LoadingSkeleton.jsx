export function SkeletonLine({ className = "" }) {
  return <div className={`animate-pulse rounded bg-parchment/10 ${className}`} />;
}

export function SkeletonCard() {
  return (
    <div className="catalog-card p-5">
      <SkeletonLine className="h-3 w-16 !bg-parchment-ink/10" />
      <SkeletonLine className="mt-3 h-5 w-3/4 !bg-parchment-ink/15" />
      <SkeletonLine className="mt-2 h-4 w-1/2 !bg-parchment-ink/10" />
      <div className="catalog-card__rule" />
      <SkeletonLine className="mt-3 h-3 w-full !bg-parchment-ink/10" />
      <SkeletonLine className="mt-2 h-3 w-5/6 !bg-parchment-ink/10" />
    </div>
  );
}

export default function LoadingSkeleton({ count = 3, variant = "card" }) {
  if (variant === "card") {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: count }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonLine key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}
