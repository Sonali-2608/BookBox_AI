import { BookOpen } from "lucide-react";

const columns = [
  {
    title: "Product",
    links: [
      { label: "How it works", href: "/#how-it-works" },
      { label: "Features", href: "/#features" },
      { label: "Bookshelf scanner", href: "/#scanner" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "#" },
      { label: "Privacy", href: "#" },
      { label: "Terms", href: "#" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-ink-line/60 bg-ink-deep">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-3">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-brass" strokeWidth={1.75} />
              <span className="font-display text-xl italic text-parchment">Lexora</span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-parchment/60">
              Your AI-powered literary companion. Built for readers who want their next book
              to actually fit them.
            </p>
          </div>

          {columns.map((col) => (
            <div key={col.title}>
              <p className="call-number text-brass/80">{col.title}</p>
              <ul className="mt-4 space-y-3">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-parchment/70 hover:text-parchment"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-4 border-t border-ink-line/60 pt-8 text-xs text-parchment/40 sm:flex-row sm:items-center">
          <span>© {new Date().getFullYear()} Lexora. All rights reserved.</span>
          <span className="font-mono">Catalogued with care.</span>
        </div>
      </div>
    </footer>
  );
}
