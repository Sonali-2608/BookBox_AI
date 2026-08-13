import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";

const SEARCH_TYPES = [
  { value: "keyword", label: "Keyword" },
  { value: "title", label: "Title" },
  { value: "author", label: "Author" },
  { value: "isbn", label: "ISBN" },
  { value: "genre", label: "Genre" },
];

export default function SearchBar({ onSearch, isLoading = false, initialQuery = "", initialType = "keyword" }) {
  const [query, setQuery] = useState(initialQuery);
  const [searchType, setSearchType] = useState(initialType);

  function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim(), searchType);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
      <div className="relative flex-1">
        <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-parchment/40" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='Try "beginner-friendly machine learning books"'
          className="w-full rounded-full border border-parchment/15 bg-ink-panel py-3 pl-11 pr-4 text-sm text-parchment placeholder:text-parchment/35 focus:border-brass/50"
        />
      </div>

      <select
        value={searchType}
        onChange={(e) => setSearchType(e.target.value)}
        className="rounded-full border border-parchment/15 bg-ink-panel px-4 py-3 text-sm text-parchment focus:border-brass/50"
      >
        {SEARCH_TYPES.map((type) => (
          <option key={type.value} value={type.value}>
            {type.label}
          </option>
        ))}
      </select>

      <button type="submit" disabled={isLoading} className="brass-btn disabled:opacity-60">
        {isLoading ? "Searching…" : "Search"}
      </button>
    </form>
  );
}
