import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, HelpCircle, Search as SearchIcon } from "lucide-react";
import ScannerUploader from "../components/ScannerUploader.jsx";
import BookCard from "../components/BookCard.jsx";

export default function Scanner() {
  const [result, setResult] = useState(null);

  return (
    <div className="mx-auto max-w-5xl">
      <span className="eyebrow">Bookshelf scanner</span>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
        Scan your shelf.
      </h1>
      <p className="mt-2 max-w-lg text-sm text-parchment/60">
        Upload a photo of your bookshelf. Lexora reads the spines, matches what it can
        against the catalog, and lets you correct anything it isn't sure about.
      </p>

      <div className="mt-8">
        <ScannerUploader onResult={setResult} />
      </div>

      {result && (
        <div className="mt-10 space-y-10">
          {result.matched.length > 0 && (
            <div>
              <h2 className="flex items-center gap-2 font-display text-lg font-medium text-parchment">
                <CheckCircle2 className="h-5 w-5 text-moss" strokeWidth={1.75} />
                Matched books ({result.matched.length})
              </h2>
              <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {result.matched.map((m, i) => (
                  <BookCard key={m.book.id} book={m.book} index={i} />
                ))}
              </div>
            </div>
          )}

          {result.unmatched.length > 0 && (
            <div>
              <h2 className="flex items-center gap-2 font-display text-lg font-medium text-parchment">
                <HelpCircle className="h-5 w-5 text-brass" strokeWidth={1.75} />
                Couldn't confidently match ({result.unmatched.length})
              </h2>
              <p className="mt-1 text-sm text-parchment/50">
                Lexora detected text here but wasn't confident about the match. Search
                manually to add these.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {result.unmatched.map((text, i) => (
                  <Link
                    key={i}
                    to={`/search?q=${encodeURIComponent(text)}&type=keyword`}
                    className="flex items-center gap-2 rounded-full border border-parchment/15 px-3 py-1.5 text-xs text-parchment/70 hover:bg-parchment/5"
                  >
                    <SearchIcon className="h-3 w-3" />
                    {text}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {result.matched.length === 0 && result.unmatched.length === 0 && (
            <p className="text-sm text-parchment/50">
              No text detected on this image — try a clearer, well-lit photo of your shelf.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
