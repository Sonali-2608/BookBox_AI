import { Link } from "react-router-dom";
import { Star, BookOpen } from "lucide-react";
import { motion } from "framer-motion";

export default function BookCard({ book, index = 0 }) {
  return (
    <motion.div
      initial={{ y: 16, opacity: 0 }}
      whileInView={{ y: 0, opacity: 1 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.4, delay: Math.min(index, 8) * 0.05 }}
    >
      <Link
        to={`/books/${book.id}`}
        className="catalog-card group flex h-full flex-col overflow-hidden p-4 transition-transform hover:-translate-y-1"
      >
        <div className="flex aspect-[2/3] w-full items-center justify-center overflow-hidden rounded bg-parchment-ink/5">
          {book.cover_url ? (
            <img
              src={book.cover_url}
              alt={book.title}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          ) : (
            <BookOpen className="h-8 w-8 text-parchment-ink/25" strokeWidth={1.5} />
          )}
        </div>

        <div className="catalog-card__rule" />

        <h3 className="mt-3 line-clamp-2 font-display text-base font-medium leading-snug text-parchment-ink">
          {book.title}
        </h3>
        <p className="mt-1 line-clamp-1 text-sm text-parchment-ink/60">
          {book.authors?.length ? book.authors.join(", ") : "Unknown author"}
        </p>

        <div className="mt-auto flex items-center justify-between pt-3">
          {book.rating ? (
            <span className="flex items-center gap-1 text-xs text-parchment-ink/70">
              <Star className="h-3.5 w-3.5 fill-brass text-brass" />
              {book.rating.toFixed(1)}
            </span>
          ) : (
            <span />
          )}
          {book.categories?.[0] && <span className="call-number">{book.categories[0]}</span>}
        </div>
      </Link>
    </motion.div>
  );
}
