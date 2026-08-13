import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  BookOpen,
  Star,
  Heart,
  BookMarked,
  CheckCircle2,
  ArrowLeft,
  Sparkles,
} from "lucide-react";
import { booksApi } from "../services/api.js";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import RecommendationCarousel from "../components/RecommendationCarousel.jsx";

function DisabledActionButton({ icon: Icon, label }) {
  return (
    <button
      disabled
      title="Coming once wishlist & reading tracking are built (Phase 9)"
      className="ghost-btn cursor-not-allowed opacity-50"
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

function MetaRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="flex justify-between border-b border-parchment/10 py-2 text-sm last:border-0">
      <span className="text-parchment/50">{label}</span>
      <span className="text-right text-parchment/85">{value}</span>
    </div>
  );
}

export default function BookDetails() {
  const { id } = useParams();
  const [book, setBook] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | not-found | error
  const [similarBooks, setSimilarBooks] = useState(null);

  useEffect(() => {
    let cancelled = false;
    let bookFetched = false;
    setStatus("loading");
    setSimilarBooks(null);

    booksApi
      .getById(id)
      .then((res) => {
        if (cancelled) return;
        bookFetched = true;
        setBook(res.data);
        setStatus("ready");
        return booksApi.getSimilar(id, 10);
      })
      .then((res) => {
        if (cancelled || !res) return;
        setSimilarBooks(res.data.results);
      })
      .catch((err) => {
        if (cancelled) return;
        if (!bookFetched) {
          setStatus(err.response?.status === 404 ? "not-found" : "error");
        } else {
          setSimilarBooks([]); // similar-books fetch failed; fail quiet, book itself is fine
        }
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (status === "loading") {
    return (
      <div className="mx-auto max-w-5xl">
        <LoadingSkeleton count={1} variant="line" />
        <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-[280px_1fr]">
          <div className="aspect-[2/3] animate-pulse rounded-lg bg-parchment/10" />
          <div className="space-y-3">
            <div className="h-8 w-2/3 animate-pulse rounded bg-parchment/10" />
            <div className="h-4 w-1/3 animate-pulse rounded bg-parchment/10" />
            <div className="h-24 w-full animate-pulse rounded bg-parchment/10" />
          </div>
        </div>
      </div>
    );
  }

  if (status === "not-found") {
    return (
      <div className="mx-auto max-w-xl py-16 text-center">
        <BookOpen className="mx-auto h-8 w-8 text-brass/50" strokeWidth={1.5} />
        <p className="mt-4 font-display text-xl font-medium text-parchment">
          We couldn't find that book.
        </p>
        <Link to="/search" className="brass-btn mt-6 inline-flex">
          Back to search
        </Link>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="mx-auto max-w-xl py-16 text-center">
        <p className="font-display text-xl font-medium text-parchment">
          Something went wrong loading this book.
        </p>
        <Link to="/search" className="brass-btn mt-6 inline-flex">
          Back to search
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <Link
        to="/search"
        className="inline-flex items-center gap-1.5 text-sm text-parchment/50 hover:text-parchment"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to search
      </Link>

      <motion.div
        initial={{ y: 16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="mt-6 grid grid-cols-1 gap-10 md:grid-cols-[280px_1fr]"
      >
        <div className="flex aspect-[2/3] items-center justify-center overflow-hidden rounded-lg bg-parchment/5 shadow-card-dark">
          {book.cover_url ? (
            <img src={book.cover_url} alt={book.title} className="h-full w-full object-cover" />
          ) : (
            <BookOpen className="h-12 w-12 text-parchment/20" strokeWidth={1.5} />
          )}
        </div>

        <div>
          {book.categories?.[0] && <span className="eyebrow">{book.categories[0]}</span>}
          <h1 className="mt-2 font-display text-3xl font-medium text-parchment sm:text-4xl">
            {book.title}
          </h1>
          <p className="mt-2 text-parchment/60">
            {book.authors?.length ? book.authors.join(", ") : "Unknown author"}
          </p>

          {book.rating && (
            <div className="mt-3 flex items-center gap-1.5">
              <Star className="h-4 w-4 fill-brass text-brass" />
              <span className="text-sm text-parchment/80">{book.rating.toFixed(1)}</span>
            </div>
          )}

          {book.description && (
            <p className="mt-6 max-w-2xl whitespace-pre-line text-sm leading-relaxed text-parchment/70">
              {book.description}
            </p>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <DisabledActionButton icon={Heart} label="Add to Wishlist" />
            <DisabledActionButton icon={BookMarked} label="Mark as Reading" />
            <DisabledActionButton icon={CheckCircle2} label="Mark as Completed" />
          </div>

          <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2">
            <div className="catalog-card p-5">
              <p className="call-number">Catalog record</p>
              <div className="catalog-card__rule" />
              <div className="mt-2">
                <MetaRow label="Pages" value={book.page_count} />
                <MetaRow label="Publisher" value={book.publisher} />
                <MetaRow label="Published" value={book.published_date} />
                <MetaRow label="ISBN" value={book.isbn} />
                <MetaRow label="Language" value={book.language?.toUpperCase()} />
              </div>
            </div>

            <div className="catalog-card flex flex-col items-center justify-center gap-2 p-5 text-center">
              <Sparkles className="h-6 w-6 text-moss-dark/50" strokeWidth={1.5} />
              <p className="font-display text-base font-medium text-parchment-ink">
                Why Lexora recommends this
              </p>
              <p className="text-xs text-parchment-ink/55">
                A personalized, AI-written explanation arrives once the reading assistant
                (Phase 7) is live.
              </p>
            </div>
          </div>

          <div className="mt-10">
            <h2 className="font-display text-lg font-medium text-parchment">Similar books</h2>
            <div className="mt-4">
              {similarBooks === null && <LoadingSkeleton count={4} />}
              {similarBooks?.length > 0 && (
                <RecommendationCarousel books={similarBooks} showReason={false} />
              )}
              {similarBooks?.length === 0 && (
                <p className="text-sm text-parchment/50">
                  No close matches in the catalog yet — search for more books and Lexora's
                  picture of what's similar will grow.
                </p>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
