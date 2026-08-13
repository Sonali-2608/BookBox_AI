import { useEffect, useState } from "react";
import { Sparkles, Heart, BookMarked, Flame, Search as SearchIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { booksApi } from "../services/api.js";
import RecommendationCarousel from "../components/RecommendationCarousel.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";

const stats = [
  { label: "Currently reading", value: 0 },
  { label: "Completed", value: 0 },
  { label: "Wishlist", value: 0 },
  { label: "Reading streak", value: "0 days" },
];

function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="catalog-card flex flex-col items-center gap-3 p-10 text-center">
      <Icon className="h-8 w-8 text-moss-dark/50" strokeWidth={1.5} />
      <p className="font-display text-lg font-medium text-parchment-ink">{title}</p>
      <p className="max-w-xs text-sm text-parchment-ink/60">{description}</p>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.name?.split(" ")[0] ?? "there";

  const [recommendations, setRecommendations] = useState(null);
  const [recsLoading, setRecsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    booksApi
      .getRecommendations(12)
      .then((res) => {
        if (!cancelled) setRecommendations(res.data.results);
      })
      .catch(() => {
        if (!cancelled) setRecommendations([]); // fail quiet — falls back to the empty state below
      })
      .finally(() => {
        if (!cancelled) setRecsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="eyebrow">Your shelf</span>
          <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
            Welcome back, {firstName}.
          </h1>
          <p className="mt-2 max-w-md text-sm text-parchment/60">
            Nothing here yet — once recommendations are live, this is where your reading life
            lives. For now, try searching for a book to add to the catalog.
          </p>
        </div>
        <Link to="/search" className="brass-btn shrink-0">
          <SearchIcon className="h-4 w-4" />
          Search books
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="catalog-card p-5">
            <p className="font-display text-2xl font-medium text-parchment-ink">{stat.value}</p>
            <p className="call-number mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="mt-10">
        <h2 className="font-display text-lg font-medium text-parchment">Recommended for you</h2>
        <div className="mt-4">
          {recsLoading && <LoadingSkeleton count={4} />}
          {!recsLoading && recommendations?.length > 0 && (
            <RecommendationCarousel books={recommendations} />
          )}
          {!recsLoading && recommendations?.length === 0 && (
            <EmptyState
              icon={Sparkles}
              title="Your recommendations are still brewing"
              description="Add a few favorite genres or authors and Lexora will start suggesting books that fit."
            />
          )}
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div>
          <h2 className="font-display text-lg font-medium text-parchment">Currently reading</h2>
          <div className="mt-4">
            <EmptyState
              icon={BookMarked}
              title="Nothing in progress"
              description="Mark a book as reading from its book page and it'll show up here."
            />
          </div>
        </div>

        <div>
          <h2 className="font-display text-lg font-medium text-parchment">Wishlist</h2>
          <div className="mt-4">
            <EmptyState
              icon={Heart}
              title="Your wishlist is empty"
              description="Save books you want to read later and they'll show up here."
            />
          </div>
        </div>

        <div>
          <h2 className="font-display text-lg font-medium text-parchment">Reading streak</h2>
          <div className="mt-4">
            <EmptyState
              icon={Flame}
              title="No streak yet"
              description="Mark a book completed and Lexora starts tracking your pace."
            />
          </div>
        </div>
      </div>
    </div>
  );
}
