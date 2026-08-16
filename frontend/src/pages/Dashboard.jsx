import { useEffect, useState } from "react";
import { Sparkles, Heart, BookMarked, Search as SearchIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { booksApi, libraryApi, userApi } from "../services/api.js";
import RecommendationCarousel from "../components/RecommendationCarousel.jsx";
import BookCard from "../components/BookCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";

function EmptyState({ icon: Icon, title, description, linkTo, linkLabel }) {
  return (
    <div className="catalog-card flex flex-col items-center gap-3 p-10 text-center">
      <Icon className="h-8 w-8 text-moss-dark/50" strokeWidth={1.5} />
      <p className="font-display text-lg font-medium text-parchment-ink">{title}</p>
      <p className="max-w-xs text-sm text-parchment-ink/60">{description}</p>
      {linkTo && (
        <Link to={linkTo} className="brass-btn mt-1">
          {linkLabel}
        </Link>
      )}
    </div>
  );
}

function BookPreviewGrid({ books }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {books.slice(0, 6).map((book, i) => (
        <BookCard key={book.id} book={book} index={i} />
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.name?.split(" ")[0] ?? "there";

  const [recommendations, setRecommendations] = useState(null);
  const [recsLoading, setRecsLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [currentlyReading, setCurrentlyReading] = useState(null);
  const [wishlistPreview, setWishlistPreview] = useState(null);

  useEffect(() => {
    let cancelled = false;

    booksApi
      .getRecommendations(12)
      .then((res) => !cancelled && setRecommendations(res.data.results))
      .catch(() => !cancelled && setRecommendations([]))
      .finally(() => !cancelled && setRecsLoading(false));

    userApi
      .getAnalytics()
      .then((res) => !cancelled && setAnalytics(res.data))
      .catch(() => {});

    libraryApi
      .getReadingHistory("reading")
      .then((res) => !cancelled && setCurrentlyReading(res.data.items.map((i) => i.book)))
      .catch(() => !cancelled && setCurrentlyReading([]));

    libraryApi
      .getWishlist()
      .then((res) => !cancelled && setWishlistPreview(res.data.items.map((i) => i.book)))
      .catch(() => !cancelled && setWishlistPreview([]));

    return () => {
      cancelled = true;
    };
  }, []);

  const stats = [
    { label: "Currently reading", value: analytics?.currently_reading ?? 0 },
    { label: "Completed", value: analytics?.books_completed ?? 0 },
    { label: "Wishlist", value: analytics?.want_to_read ?? 0 },
    { label: "Reading streak", value: `${analytics?.reading_streak_days ?? 0} days` },
  ];

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="eyebrow">Your shelf</span>
          <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
            Welcome back, {firstName}.
          </h1>
          <p className="mt-2 max-w-md text-sm text-parchment/60">
            Your reading life, in one place.
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
              linkTo="/preferences"
              linkLabel="Set preferences"
            />
          )}
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-medium text-parchment">
              Currently reading
            </h2>
            {currentlyReading?.length > 0 && (
              <Link to="/reading" className="text-xs text-parchment/50 hover:text-parchment">
                View all
              </Link>
            )}
          </div>
          <div className="mt-4">
            {currentlyReading === null && <LoadingSkeleton count={3} />}
            {currentlyReading?.length === 0 && (
              <EmptyState
                icon={BookMarked}
                title="Nothing in progress"
                description="Mark a book as reading from its book page and it'll show up here."
              />
            )}
            {currentlyReading?.length > 0 && <BookPreviewGrid books={currentlyReading} />}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-medium text-parchment">Wishlist</h2>
            {wishlistPreview?.length > 0 && (
              <Link to="/wishlist" className="text-xs text-parchment/50 hover:text-parchment">
                View all
              </Link>
            )}
          </div>
          <div className="mt-4">
            {wishlistPreview === null && <LoadingSkeleton count={3} />}
            {wishlistPreview?.length === 0 && (
              <EmptyState
                icon={Heart}
                title="Your wishlist is empty"
                description="Save books you want to read later and they'll show up here."
              />
            )}
            {wishlistPreview?.length > 0 && <BookPreviewGrid books={wishlistPreview} />}
          </div>
        </div>
      </div>
    </div>
  );
}
