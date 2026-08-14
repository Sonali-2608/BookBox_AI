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
import { booksApi, aiApi } from "../services/api.js";
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
  const [whyExplanation, setWhyExplanation] = useState(null);
  const [whyLoading, setWhyLoading] = useState(true);
  const [summaryData, setSummaryData] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setSimilarBooks(null);
    setWhyExplanation(null);
    setWhyLoading(true);
    setSummaryData(null);
    setSummaryLoading(true);

    booksApi
      .getById(id)
      .then((res) => {
        if (cancelled) return;
        setBook(res.data);
        setStatus("ready");

        // These three are independent — fire in parallel, each with its
        // own quiet failure so one slow/broken AI call doesn't block the
        // others or the book itself from rendering.
        booksApi
          .getSimilar(id, 10)
          .then((r) => !cancelled && setSimilarBooks(r.data.results))
          .catch(() => !cancelled && setSimilarBooks([]));

        aiApi
          .getWhy(id)
          .then((r) => !cancelled && setWhyExplanation(r.data.explanation))
          .catch(() => !cancelled && setWhyExplanation(null))
          .finally(() => !cancelled && setWhyLoading(false));

        aiApi
          .getSummary(id)
          .then((r) => !cancelled && setSummaryData(r.data))
          .catch(() => !cancelled && setSummaryData(null))
          .finally(() => !cancelled && setSummaryLoading(false));
      })
      .catch((err) => {
        if (cancelled) return;
        setStatus(err.response?.status === 404 ? "not-found" : "error");
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
              {whyLoading && <p className="text-xs text-parchment-ink/40">Thinking…</p>}
              {!whyLoading && whyExplanation && (
                <p className="text-sm text-parchment-ink/75">{whyExplanation}</p>
              )}
              {!whyLoading && !whyExplanation && (
                <p className="text-xs text-parchment-ink/55">
                  Add a few favorite genres or authors and Lexora can explain why a book fits
                  you.
                </p>
              )}
            </div>
          </div>

          <div className="mt-10">
            <h2 className="font-display text-lg font-medium text-parchment">AI summary</h2>
            <div className="mt-4">
              {summaryLoading && <LoadingSkeleton count={1} variant="line" />}
              {!summaryLoading && summaryData?.summary && (
                <div className="catalog-card p-6">
                  <p className="text-sm leading-relaxed text-parchment-ink/80">
                    {summaryData.summary}
                  </p>

                  {summaryData.key_takeaways?.length > 0 && (
                    <>
                      <div className="catalog-card__rule" />
                      <p className="call-number mt-3">Key takeaways</p>
                      <ul className="mt-2 space-y-1.5">
                        {summaryData.key_takeaways.map((takeaway, i) => (
                          <li
                            key={i}
                            className="flex gap-2 text-sm text-parchment-ink/75"
                          >
                            <span className="text-brass-dark">•</span>
                            {takeaway}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  {summaryData.target_audience && (
                    <>
                      <div className="catalog-card__rule" />
                      <p className="call-number mt-3">Who it's for</p>
                      <p className="mt-1 text-sm text-parchment-ink/75">
                        {summaryData.target_audience}
                      </p>
                    </>
                  )}
                </div>
              )}
              {!summaryLoading && !summaryData?.summary && (
                <p className="text-sm text-parchment/50">
                  No AI summary available for this book yet.
                </p>
              )}
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
