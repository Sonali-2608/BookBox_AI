import { useState } from "react";
import { SearchX, AlertCircle } from "lucide-react";
import SearchBar from "../components/SearchBar.jsx";
import BookCard from "../components/BookCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import { booksApi } from "../services/api.js";

export default function Search() {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [source, setSource] = useState(null);
  const [lastQuery, setLastQuery] = useState("");

  async function handleSearch(query, searchType) {
    setIsLoading(true);
    setError(null);
    setLastQuery(query);
    try {
      const res = await booksApi.search(query, searchType);
      setResults(res.data.results);
      setSource(res.data.source);
    } catch {
      setError("Something went wrong reaching the book catalog. Please try again.");
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <span className="eyebrow">Search</span>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
        Find your next book.
      </h1>
      <p className="mt-2 max-w-lg text-sm text-parchment/60">
        Search by title, author, ISBN, or genre. Full natural-language semantic search lands
        once the recommendation engine is built.
      </p>

      <div className="mt-8">
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      </div>

      <div className="mt-10">
        {isLoading && <LoadingSkeleton count={6} />}

        {!isLoading && error && (
          <div className="catalog-card flex flex-col items-center gap-3 p-10 text-center">
            <AlertCircle className="h-8 w-8 text-brass-dark" strokeWidth={1.5} />
            <p className="font-display text-lg font-medium text-parchment-ink">{error}</p>
          </div>
        )}

        {!isLoading && !error && results !== null && results.length === 0 && (
          <div className="catalog-card flex flex-col items-center gap-3 p-10 text-center">
            <SearchX className="h-8 w-8 text-moss-dark/50" strokeWidth={1.5} />
            <p className="font-display text-lg font-medium text-parchment-ink">
              No matches for "{lastQuery}"
            </p>
            <p className="max-w-xs text-sm text-parchment-ink/60">
              Try a different search type, or check the spelling of the title or author.
            </p>
          </div>
        )}

        {!isLoading && !error && results && results.length > 0 && (
          <>
            <p className="mb-4 font-mono text-xs uppercase tracking-wide text-parchment/40">
              {results.length} result{results.length === 1 ? "" : "s"}
              {source && source !== "none" ? ` · via ${source.replace("_", " ")}` : ""}
            </p>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {results.map((book, i) => (
                <BookCard key={book.id} book={book} index={i} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
