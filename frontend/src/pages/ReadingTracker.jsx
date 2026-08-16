import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BookMarked, CheckCircle2, BookOpen } from "lucide-react";
import { libraryApi } from "../services/api.js";
import BookCard from "../components/BookCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";

const TABS = [
  { key: "reading", label: "Currently reading", icon: BookMarked },
  { key: "completed", label: "Completed", icon: CheckCircle2 },
  { key: "want_to_read", label: "Want to read", icon: BookOpen },
];

export default function ReadingTracker() {
  const [tab, setTab] = useState("reading");
  const [items, setItems] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setItems(null);
    libraryApi
      .getReadingHistory(tab)
      .then((res) => !cancelled && setItems(res.data.items))
      .catch(() => !cancelled && setItems([]));
    return () => {
      cancelled = true;
    };
  }, [tab]);

  return (
    <div className="mx-auto max-w-6xl">
      <span className="eyebrow">Reading tracker</span>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
        Your reading, tracked.
      </h1>

      <div className="mt-6 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm transition-colors ${
              tab === t.key
                ? "bg-brass text-ink"
                : "border border-parchment/15 text-parchment/70 hover:bg-parchment/5"
            }`}
          >
            <t.icon className="h-4 w-4" strokeWidth={1.75} />
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-8">
        {items === null && <LoadingSkeleton count={6} />}

        {items?.length === 0 && (
          <div className="catalog-card flex flex-col items-center gap-3 p-10 text-center">
            <p className="font-display text-lg font-medium text-parchment-ink">
              Nothing here yet
            </p>
            <p className="max-w-xs text-sm text-parchment-ink/60">
              Mark a book from its details page and it'll show up here.
            </p>
            <Link to="/search" className="brass-btn mt-2">
              Search books
            </Link>
          </div>
        )}

        {items?.length > 0 && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {items.map((item, i) => (
              <BookCard key={item.book.id} book={item.book} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
