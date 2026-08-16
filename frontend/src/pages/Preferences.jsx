import { useEffect, useState } from "react";
import { X, Plus } from "lucide-react";
import { userApi } from "../services/api.js";

const GENRE_OPTIONS = [
  "Fiction",
  "Fantasy",
  "Romance",
  "Thriller",
  "Mystery",
  "Science",
  "Technology",
  "Self Help",
  "Biography",
  "Business",
  "History",
];

const FREQUENCY_OPTIONS = [
  { value: "daily", label: "Daily" },
  { value: "several_times_a_week", label: "Several times a week" },
  { value: "weekly", label: "Weekly" },
  { value: "occasionally", label: "Occasionally" },
];

const LENGTH_OPTIONS = [
  { value: "short", label: "Short" },
  { value: "medium", label: "Medium" },
  { value: "long", label: "Long" },
];

export default function Preferences() {
  const [genres, setGenres] = useState([]);
  const [authors, setAuthors] = useState([]);
  const [authorInput, setAuthorInput] = useState("");
  const [frequency, setFrequency] = useState(null);
  const [length, setLength] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    userApi
      .getPreferences()
      .then((res) => {
        if (cancelled) return;
        setGenres(res.data.favorite_genres);
        setAuthors(res.data.favorite_authors);
        setFrequency(res.data.reading_frequency);
        setLength(res.data.preferred_length);
      })
      .finally(() => !cancelled && setIsLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleGenre(genre) {
    setSaved(false);
    setGenres((prev) => (prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]));
  }

  function addAuthor() {
    const name = authorInput.trim();
    if (!name || authors.includes(name)) return;
    setSaved(false);
    setAuthors((prev) => [...prev, name]);
    setAuthorInput("");
  }

  function removeAuthor(name) {
    setSaved(false);
    setAuthors((prev) => prev.filter((a) => a !== name));
  }

  async function handleSave() {
    setIsSaving(true);
    try {
      await userApi.updatePreferences({
        favorite_genres: genres,
        favorite_authors: authors,
        reading_frequency: frequency,
        preferred_length: length,
      });
      setSaved(true);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl">
        <p className="text-sm text-parchment/50">Loading…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <span className="eyebrow">Preferences</span>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
        Tell Lexora what you love.
      </h1>
      <p className="mt-2 text-sm text-parchment/60">
        This powers your recommendations and the "why Lexora recommends this" explanations.
      </p>

      <div className="mt-8 space-y-8">
        <div>
          <h2 className="font-display text-base font-medium text-parchment">Favorite genres</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {GENRE_OPTIONS.map((genre) => (
              <button
                key={genre}
                onClick={() => toggleGenre(genre)}
                className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
                  genres.includes(genre)
                    ? "bg-brass text-ink"
                    : "border border-parchment/15 text-parchment/70 hover:bg-parchment/5"
                }`}
              >
                {genre}
              </button>
            ))}
          </div>
        </div>

        <div>
          <h2 className="font-display text-base font-medium text-parchment">Favorite authors</h2>
          <div className="mt-3 flex gap-2">
            <input
              value={authorInput}
              onChange={(e) => setAuthorInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addAuthor();
                }
              }}
              placeholder="e.g. James Clear"
              className="flex-1 rounded-full border border-parchment/15 bg-ink-panel px-4 py-2 text-sm text-parchment placeholder:text-parchment/35 focus:border-brass/50"
            />
            <button onClick={addAuthor} className="ghost-btn !px-3" aria-label="Add author">
              <Plus className="h-4 w-4" />
            </button>
          </div>
          {authors.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {authors.map((author) => (
                <span
                  key={author}
                  className="flex items-center gap-1.5 rounded-full bg-parchment/10 px-3 py-1.5 text-sm text-parchment/80"
                >
                  {author}
                  <button onClick={() => removeAuthor(author)} aria-label={`Remove ${author}`}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2 className="font-display text-base font-medium text-parchment">Reading frequency</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {FREQUENCY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => {
                  setSaved(false);
                  setFrequency(opt.value);
                }}
                className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
                  frequency === opt.value
                    ? "bg-brass text-ink"
                    : "border border-parchment/15 text-parchment/70 hover:bg-parchment/5"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <h2 className="font-display text-base font-medium text-parchment">
            Preferred book length
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {LENGTH_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => {
                  setSaved(false);
                  setLength(opt.value);
                }}
                className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
                  length === opt.value
                    ? "bg-brass text-ink"
                    : "border border-parchment/15 text-parchment/70 hover:bg-parchment/5"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={handleSave} disabled={isSaving} className="brass-btn disabled:opacity-60">
            {isSaving ? "Saving…" : "Save preferences"}
          </button>
          {saved && <span className="text-sm text-moss">Saved.</span>}
        </div>
      </div>
    </div>
  );
}
