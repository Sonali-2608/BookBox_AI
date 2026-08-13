import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Menu, X, BookOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../hooks/useAuth.js";
import GoogleSignInButton from "./GoogleSignInButton.jsx";

const navLinks = [
  { label: "How it works", href: "/#how-it-works" },
  { label: "Features", href: "/#features" },
  { label: "Scanner", href: "/#scanner" },
];

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 border-b border-ink-line/60 bg-ink/80 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-brass" strokeWidth={1.75} />
          <span className="font-display text-xl italic tracking-tight text-parchment">
            Lexora
          </span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-parchment/70 transition-colors hover:text-parchment"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="hidden items-center gap-4 md:flex">
          {isAuthenticated ? (
            <>
              <NavLink
                to="/dashboard"
                className="text-sm font-medium text-parchment/80 hover:text-parchment"
              >
                Dashboard
              </NavLink>
              {user?.profile_image ? (
                <img
                  src={user.profile_image}
                  alt={user.name}
                  className="h-8 w-8 rounded-full border border-brass/40"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brass/20 font-mono text-xs text-brass">
                  {user?.name?.[0]?.toUpperCase() ?? "?"}
                </div>
              )}
              <button
                onClick={async () => {
                  await logout();
                  navigate("/");
                }}
                className="text-sm text-parchment/60 hover:text-parchment"
              >
                Sign out
              </button>
            </>
          ) : (
            <GoogleSignInButton />
          )}
        </div>

        <button
          className="md:hidden"
          onClick={() => setMobileOpen((v) => !v)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-ink-line/60 bg-ink md:hidden"
          >
            <div className="flex flex-col gap-4 px-6 py-6">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-parchment/80"
                >
                  {link.label}
                </a>
              ))}
              <div className="pt-2">
                {isAuthenticated ? (
                  <Link to="/dashboard" className="brass-btn w-full">
                    Go to Dashboard
                  </Link>
                ) : (
                  <GoogleSignInButton />
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
