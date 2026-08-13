import BookCard from "./BookCard.jsx";

export default function RecommendationCarousel({ books, showReason = true }) {
  if (!books?.length) return null;

  return (
    <div className="-mx-1 flex gap-4 overflow-x-auto px-1 pb-2">
      {books.map((book, i) => (
        <div key={book.id} className="w-40 shrink-0">
          <BookCard book={book} index={i} />
          {showReason && book.reason && (
            <p className="mt-2 line-clamp-2 text-xs text-parchment/50">{book.reason}</p>
          )}
        </div>
      ))}
    </div>
  );
}
