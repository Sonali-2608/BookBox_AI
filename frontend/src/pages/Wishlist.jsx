import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Heart } from "lucide-react";
import { libraryApi } from "../services/api.js";
import BookCard from "../components/BookCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";

export default function Wishlist() {
  const [items, setItems] = useState(null);

  useEffect(() => {
    let cancelled = false;
    libraryApi
      .getWishlist()
      .then((res) => !cancelled && setItems(res.data.items))
      .catch(() => !cancelled && setItems([]));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl">
      <span className="eyebrow">Wishlist</span>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">Want to read.</h1>
      <p className="mt-2 text-sm text-parchment/60">
        Books you've saved for later. Move one to "Reading" from its details page once you
        start it.
      </p>

      <div className="mt-8">
        {items === null && <LoadingSkeleton count={6} />}

        {items?.length === 0 && (
          <div className="catalog-card flex flex-col items-center gap-3 p-10 text-center">
            <Heart className="h-8 w-8 text-moss-dark/50" strokeWidth={1.5} />
            <p className="font-display text-lg font-medium text-parchment-ink">
              Your wishlist is empty
            </p>
            <p className="max-w-xs text-sm text-parchment-ink/60">
              Search for books and add ones you want to read.
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
