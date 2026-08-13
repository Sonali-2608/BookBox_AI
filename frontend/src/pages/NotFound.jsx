import { Link } from "react-router-dom";
import { BookX } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6 text-center">
      <BookX className="h-10 w-10 text-brass/60" strokeWidth={1.5} />
      <p className="call-number mt-4 !text-brass/70">Error · 404</p>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
        This page isn't in the catalog.
      </h1>
      <p className="mt-3 max-w-sm text-sm text-parchment/60">
        The page you're looking for doesn't exist, or it's been moved.
      </p>
      <Link to="/" className="brass-btn mt-8">
        Back to Lexora
      </Link>
    </div>
  );
}
